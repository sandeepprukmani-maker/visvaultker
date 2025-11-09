import type { Express } from "express";
import { createServer, type Server } from "http";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";
import { 
  automationRequestSchema, 
  unifiedAutomationRequestSchema,
  type AutomationResponse, 
  type LogEntry,
  type AutomationMode 
} from "@shared/schema";
import { randomUUID } from "crypto";
import { setupWebSocket, broadcastToSession } from "./websocket";
import { parsePrompt, generateCodeForMode } from "./intelligent-router";

export async function registerRoutes(app: Express): Promise<Server> {
  app.post("/api/automate", async (req, res) => {
    try {
      const validatedData = automationRequestSchema.parse(req.body);
      const sessionId = randomUUID();
      const logs: LogEntry[] = [];

      // Helper to add log entries
      const addLog = (action: string, status: LogEntry["status"], selector?: string, description?: string) => {
        logs.push({
          id: randomUUID(),
          timestamp: Date.now(),
          action,
          status,
          selector,
          description,
        });
      };

      addLog("Initializing browser session", "running", undefined, `Using model: ${validatedData.model}`);

      // Initialize Stagehand with headed browser (visible window)
      const stagehand = new Stagehand({
        env: "LOCAL",
        modelName: validatedData.model,
        enableCaching: true,
        localBrowserLaunchOptions: {
          headless: false,
        },
      });

      try {
        await stagehand.init();
        addLog("Browser session initialized", "success");

        const page = stagehand.context.pages()[0];
        
        // Navigate to URL
        addLog(`Navigating to ${validatedData.url}`, "running");
        await page.goto(validatedData.url, { waitUntil: "networkidle" });
        addLog(`Loaded ${validatedData.url}`, "success");

        let result: any;
        let generatedCode = "";

        // Execute based on mode
        switch (validatedData.mode) {
          case "act":
            addLog(`Executing action: ${validatedData.prompt}`, "running");
            result = await (stagehand as any).act(validatedData.prompt);
            addLog("Action completed", "success", undefined, "Element interacted successfully");
            
            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("${validatedData.url}");
await stagehand.act("${validatedData.prompt}");

await stagehand.close();`;
            break;

          case "observe":
            addLog(`Observing: ${validatedData.prompt}`, "running");
            result = await (stagehand as any).observe(validatedData.prompt);
            addLog("Observation completed", "success", undefined, JSON.stringify(result, null, 2));
            
            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("${validatedData.url}");
const result = await stagehand.observe("${validatedData.prompt}");
console.log("Observed:", result);

await stagehand.close();`;
            break;

          case "extract":
            addLog(`Extracting: ${validatedData.prompt}`, "running");
            // For extract, we need a schema - use a generic one for demo
            const extractSchema = z.object({
              data: z.string().describe(validatedData.prompt)
            });
            result = await (stagehand as any).extract(validatedData.prompt, extractSchema);
            addLog("Extraction completed", "success", undefined, JSON.stringify(result, null, 2));
            
            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("${validatedData.url}");

const schema = z.object({
  data: z.string().describe("${validatedData.prompt}")
});

const result = await stagehand.extract("${validatedData.prompt}", schema);
console.log("Extracted:", result);

await stagehand.close();`;
            break;

          case "agent":
            addLog(`Running agent: ${validatedData.prompt}`, "running");
            const agent = (stagehand as any).agent({
              model: validatedData.model,
              systemPrompt: "You're a helpful assistant that can control a web browser.",
            });
            result = await agent.execute(validatedData.prompt);
            addLog("Agent task completed", "success", undefined, "Multi-step task executed");
            
            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("${validatedData.url}");

const agent = stagehand.agent({
  cua: true,
  model: "${validatedData.model}",
  systemPrompt: "You're a helpful assistant that can control a web browser.",
});

const result = await agent.execute("${validatedData.prompt}");
console.log("Agent result:", result);

await stagehand.close();`;
            break;
        }

        await stagehand.close();
        addLog("Browser session closed", "success");

        const response: AutomationResponse = {
          success: true,
          sessionId,
          logs,
          generatedCode: {
            typescript: generatedCode,
          },
        };

        res.json(response);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        addLog("Automation failed", "error", undefined, errorMessage);
        
        await stagehand.close().catch(() => {}); // Try to clean up

        const response: AutomationResponse = {
          success: false,
          sessionId,
          logs,
          generatedCode: {},
          error: errorMessage,
        };

        res.status(500).json(response);
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({
          success: false,
          error: "Invalid request data",
          details: error.errors,
        });
      } else {
        res.status(500).json({
          success: false,
          error: error instanceof Error ? error.message : "Internal server error",
        });
      }
    }
  });

  // New unified automation endpoint with live WebSocket updates
  app.post("/api/automate-unified", async (req, res) => {
    try {
      const validatedData = unifiedAutomationRequestSchema.parse(req.body);
      const sessionId = randomUUID();
      const logs: LogEntry[] = [];
      const usedModes: AutomationMode[] = [];

      // Helper to add log entries and broadcast via WebSocket
      const addLog = (action: string, status: LogEntry["status"], selector?: string, description?: string) => {
        const log: LogEntry = {
          id: randomUUID(),
          timestamp: Date.now(),
          action,
          status,
          selector,
          description,
        };
        logs.push(log);
        
        // Broadcast to WebSocket clients
        broadcastToSession(sessionId, {
          type: "log",
          sessionId,
          log,
        });
      };

      // Send initial response with sessionId
      res.json({ sessionId });

      // Parse the prompt to extract URL and determine mode
      let parsedPrompt;
      try {
        parsedPrompt = parsePrompt(validatedData.prompt);
        addLog(
          "Analyzed prompt",
          "success",
          undefined,
          `URL: ${parsedPrompt.url} | Mode: ${parsedPrompt.suggestedMode} | ${parsedPrompt.reasoning}`
        );
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Failed to parse prompt";
        addLog("Prompt analysis failed", "error", undefined, errorMessage);
        broadcastToSession(sessionId, {
          type: "error",
          sessionId,
          error: errorMessage,
        });
        return;
      }

      addLog("Initializing browser session", "running", undefined, `Using model: ${validatedData.model}`);

      // Initialize Stagehand
      const stagehand = new Stagehand({
        env: "LOCAL",
        modelName: validatedData.model,
        enableCaching: true,
        localBrowserLaunchOptions: {
          headless: false,
        },
      });

      try {
        await stagehand.init();
        addLog("Browser session initialized", "success");

        const page = stagehand.context.pages()[0];
        
        // Navigate to URL
        addLog(`Navigating to ${parsedPrompt.url}`, "running");
        await page.goto(parsedPrompt.url, { waitUntil: "networkidle" });
        addLog(`Loaded ${parsedPrompt.url}`, "success");

        let result: any;
        const mode = parsedPrompt.suggestedMode;
        usedModes.push(mode);

        // Execute based on suggested mode
        switch (mode) {
          case "act":
            addLog(`Executing action: ${parsedPrompt.task}`, "running");
            result = await (stagehand as any).act(parsedPrompt.task);
            addLog("Action completed", "success", undefined, "Element interacted successfully");
            break;

          case "observe":
            addLog(`Observing: ${parsedPrompt.task}`, "running");
            result = await (stagehand as any).observe(parsedPrompt.task);
            addLog(
              "Observation completed",
              "success",
              undefined,
              `Found ${Array.isArray(result) ? result.length : 0} elements`
            );
            break;

          case "extract":
            addLog(`Extracting: ${parsedPrompt.task}`, "running");
            const extractSchema = z.object({
              data: z.string().describe(parsedPrompt.task)
            });
            result = await (stagehand as any).extract(parsedPrompt.task, extractSchema);
            addLog("Extraction completed", "success", undefined, JSON.stringify(result, null, 2));
            break;

          case "agent":
            addLog(`Running agent: ${parsedPrompt.task}`, "running");
            const agent = (stagehand as any).agent({
              model: validatedData.model,
              systemPrompt: "You're a helpful automation assistant that can control a web browser.",
            });
            result = await agent.execute(parsedPrompt.task);
            addLog(
              "Agent task completed",
              "success",
              undefined,
              `Completed: ${result.completed} | ${result.message}`
            );
            break;
        }

        await stagehand.close();
        addLog("Browser session closed", "success");

        const generatedCode = generateCodeForMode(
          mode,
          parsedPrompt.url,
          parsedPrompt.task,
          validatedData.model
        );

        const response: AutomationResponse = {
          success: true,
          sessionId,
          logs,
          generatedCode: {
            typescript: generatedCode,
          },
          detectedUrl: parsedPrompt.url,
          usedModes,
        };

        broadcastToSession(sessionId, {
          type: "complete",
          sessionId,
          response,
        });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        addLog("Automation failed", "error", undefined, errorMessage);
        
        await stagehand.close().catch(() => {});

        broadcastToSession(sessionId, {
          type: "error",
          sessionId,
          error: errorMessage,
        });
      }
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({
          success: false,
          error: "Invalid request data",
          details: error.errors,
        });
      } else {
        res.status(500).json({
          success: false,
          error: error instanceof Error ? error.message : "Internal server error",
        });
      }
    }
  });

  const httpServer = createServer(app);
  
  // Setup WebSocket server
  setupWebSocket(httpServer);
  
  return httpServer;
}
