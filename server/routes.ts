import type { Express } from "express";
import { createServer, type Server } from "http";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";
import { automationRequestSchema, type AutomationResponse, type LogEntry } from "@shared/schema";
import { randomUUID } from "crypto";

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

  const httpServer = createServer(app);
  return httpServer;
}
