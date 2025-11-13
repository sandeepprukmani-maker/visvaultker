import type { Express } from "express";
import { createServer, type Server } from "http";
import { Stagehand, type AvailableModel } from "@browserbasehq/stagehand";
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
import { findSimilarAutomation, saveAutomation } from "./semantic-cache";
import { StagehandStep, emitLocatorScript, normalizeStep } from "./locator-generator";
import { CustomLLMClient } from "./custom-llm-client";

function createStagehandInstance(modelName: string) {
  const customClient = new CustomLLMClient({
    modelName: modelName as AvailableModel,
    apiEndpoint: process.env.CUSTOM_LLM_API_ENDPOINT!,
    actualModelName: process.env.CUSTOM_LLM_MODEL_NAME || "gpt-4o-1-2025-04-14-eastus-dz",
  });

  return new Stagehand({
    env: "LOCAL",
    enableCaching: true,
    localBrowserLaunchOptions: {
      headless: false,
    },
    llmClient: customClient,
  });
}

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

      // Initialize Stagehand with custom or default LLM client
      const stagehand = createStagehandInstance(validatedData.model);

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
      console.log("===== AUTOMATION STARTING FOR SESSION:", sessionId, "=====");

      // Wrap the async continuation in a promise to catch errors
      (async () => {
        try {
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
            console.error("Prompt parsing error:", errorMessage);
            addLog("Prompt analysis failed", "error", undefined, errorMessage);
            broadcastToSession(sessionId, {
              type: "error",
              sessionId,
              error: errorMessage,
            });
            return;
          }

      // Check semantic cache for similar automation
      addLog("Checking cache for similar automations", "running");
      const cachedAutomation = await findSimilarAutomation(
        validatedData.prompt,
        parsedPrompt.url
      );

      if (cachedAutomation) {
        addLog(
          "Cache hit!",
          "success",
          undefined,
          `Found similar automation (${Math.round(cachedAutomation.similarity * 100)}% match). Reusing cached result - 0 AI usage!`
        );

        const response: AutomationResponse = {
          success: true,
          sessionId,
          logs: [...logs, ...cachedAutomation.automation.logs],
          generatedCode: {
            ...cachedAutomation.automation.generatedCode,
            cached: "This result was retrieved from semantic cache - no AI credits used!",
          },
          detectedUrl: cachedAutomation.automation.detectedUrl || parsedPrompt.url,
          usedModes: [cachedAutomation.automation.mode as AutomationMode],
          screenshot: cachedAutomation.automation.screenshot || undefined,
        };

        broadcastToSession(sessionId, {
          type: "complete",
          sessionId,
          response,
        });
        return;
      }

      addLog("No cache hit, executing automation", "running");

      addLog("Initializing browser session", "running", undefined, `Using model: ${validatedData.model}`);

      // Initialize Stagehand with custom or default LLM client
      const stagehand = createStagehandInstance(validatedData.model);

      try {
        await stagehand.init();
        addLog("Browser session initialized", "success");

        const page = stagehand.context.pages()[0];
        const capturedSteps: StagehandStep[] = [];

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
            addLog(`Observing target element for: ${parsedPrompt.task}`, "running");
            // Use observe to get selector info before acting
            let observeResults: any[] = [];
            try {
              observeResults = await (stagehand as any).observe(parsedPrompt.task);
            } catch (observeError) {
              console.log("Observe failed, will use direct act():", observeError);
            }

            if (Array.isArray(observeResults) && observeResults.length > 0) {
              const firstResult = observeResults[0];
              addLog(`Found element: ${firstResult.description || 'target'}`, "success", firstResult.selector);

              // Capture step for locator generation
              const step = normalizeStep(
                firstResult.method || firstResult.action || 'click',
                firstResult.selector,
                firstResult.description,
                firstResult.arguments?.[0]
              );
              capturedSteps.push(step);

              // Highlight element before interacting
              try {
                if (firstResult.selector) {
                  const locator = page.locator(firstResult.selector);
                  await locator.highlight();
                  await page.waitForTimeout(1000); // Wait to show highlight
                  addLog("Element highlighted", "success", firstResult.selector);
                }
              } catch (highlightError) {
                console.log("Could not highlight element:", highlightError);
              }

              // Act on the observed element
              addLog(`Executing action: ${parsedPrompt.task}`, "running");
              result = await (stagehand as any).act(firstResult);
              addLog("Action completed", "success", undefined, "Element interacted successfully");
            } else {
              // Fallback to direct act if observe fails
              addLog(`Executing action directly: ${parsedPrompt.task}`, "running");
              result = await (stagehand as any).act(parsedPrompt.task);

              // Still capture the action even without a specific selector
              // Note: This step won't have a selector, so generated code will be a comment
              capturedSteps.push({
                action: "click",
                description: `Action performed (selector not captured): ${parsedPrompt.task}`,
              });

              addLog("Action completed", "success", undefined, "Element interacted successfully (selector not captured for rerunnable code)");
            }
            break;

          case "observe":
            addLog(`Observing: ${parsedPrompt.task}`, "running");
            result = await (stagehand as any).observe(parsedPrompt.task);

            // Capture observe results and highlight found elements
            if (Array.isArray(result)) {
              for (const obs of result) {
                const step = normalizeStep(
                  obs.method || obs.action || 'click',
                  obs.selector,
                  obs.description
                );
                capturedSteps.push(step);

                // Highlight each observed element
                try {
                  if (obs.selector) {
                    const locator = page.locator(obs.selector);
                    await locator.highlight();
                    await page.waitForTimeout(1500); // Wait to show highlight
                  }
                } catch (highlightError) {
                  console.log("Could not highlight observed element:", highlightError);
                }
              }
            }

            addLog(
              "Observation completed",
              "success",
              undefined,
              `Found and highlighted ${Array.isArray(result) ? result.length : 0} elements`
            );
            break;

          case "extract":
            addLog(`Extracting: ${parsedPrompt.task}`, "running");
            const extractSchema = z.object({
              data: z.string().describe(parsedPrompt.task)
            });
            result = await (stagehand as any).extract(parsedPrompt.task, extractSchema);

            // Capture extract step (doesn't have specific selectors, but note the action)
            capturedSteps.push({
              action: "extract",
              description: parsedPrompt.task,
            });

            addLog("Extraction completed", "success", undefined, JSON.stringify(result, null, 2));
            break;

          case "agent":
            addLog(`Running agent: ${parsedPrompt.task}`, "running");
            const agent = (stagehand as any).agent({
              model: validatedData.model,
              systemPrompt: "You're a helpful automation assistant that can control a web browser.",
            });
            result = await agent.execute({
              instruction: parsedPrompt.task,
              highlightCursor: true, // Enable visual cursor to show interactions
            });

            // For agent, we note it as a multi-step workflow
            capturedSteps.push({
              action: "agent" as any,
              description: `Agent workflow: ${parsedPrompt.task}`,
            });

            addLog(
              "Agent task completed",
              "success",
              undefined,
              `Completed: ${result.completed} | ${result.message}`
            );
            break;
        }

        // Capture screenshot before closing
        addLog("Capturing screenshot", "running");
        let screenshot: string | null = null;
        try {
          const screenshotBuffer = await page.screenshot({
            type: 'png',
            fullPage: false,
          });
          screenshot = screenshotBuffer.toString('base64');
          addLog("Screenshot captured", "success");
        } catch (screenshotError) {
          console.error("Failed to capture screenshot:", screenshotError);
          addLog("Screenshot capture failed", "error", undefined, "Non-critical error");
        }

        await stagehand.close();
        addLog("Browser session closed", "success");

        const generatedCode = generateCodeForMode(
          mode,
          parsedPrompt.url,
          parsedPrompt.task,
          validatedData.model
        );

        // Generate locator-based rerunnable code
        let locatorCode = '';
        if (capturedSteps.length > 0) {
          addLog("Generating rerunnable locator code", "running");
          try {
            locatorCode = emitLocatorScript({
              url: parsedPrompt.url,
              model: validatedData.model,
              mode,
              steps: capturedSteps,
            });
            addLog("Generated rerunnable code with locators", "success");
          } catch (locatorError) {
            console.error("Failed to generate locator code:", locatorError);
            addLog("Locator code generation failed", "error", undefined, "Non-critical error");
          }
        }

        const response: AutomationResponse = {
          success: true,
          sessionId,
          logs,
          generatedCode: {
            typescript: generatedCode,
            locators: locatorCode || undefined,
          },
          detectedUrl: parsedPrompt.url,
          usedModes,
          screenshot: screenshot ? `data:image/png;base64,${screenshot}` : undefined,
        };

        // Save to semantic cache for future reuse
        await saveAutomation({
          prompt: validatedData.prompt,
          detectedUrl: parsedPrompt.url,
          mode,
          model: validatedData.model,
          success: true,
          sessionId,
          logs,
          generatedCode: {
            typescript: generatedCode,
            locators: locatorCode || undefined,
          },
          screenshot: screenshot ? `data:image/png;base64,${screenshot}` : null,
          error: null,
        });

        addLog("Saved to cache", "success", undefined, "Future similar prompts will reuse this automation!");

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
        } catch (asyncError) {
          console.error("Automation async error:", asyncError);
          const errorMessage = asyncError instanceof Error ? asyncError.message : "Unknown error occurred";
          broadcastToSession(sessionId, {
            type: "error",
            sessionId,
            error: errorMessage,
          });
        }
      })().catch(err => console.error("Fatal async error:", err));
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

  // History management routes
  app.get("/api/history", async (req, res) => {
    try {
      const { fetchAllHistory } = await import("./api-client");
      const history = await fetchAllHistory();

      res.json({ success: true, history });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch history",
      });
    }
  });

  app.delete("/api/history/:id", async (req, res) => {
    try {
      const { deleteHistory } = await import("./api-client");

      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ success: false, error: "Invalid ID" });
      }

      const result = await deleteHistory(id);

      res.json({ success: true, message: result.message });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete history item",
      });
    }
  });

  app.delete("/api/history", async (req, res) => {
    try {
      const { deleteAllHistory } = await import("./api-client");

      const result = await deleteAllHistory();

      res.json({ success: true, message: result.message });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : "Failed to delete all history",
      });
    }
  });

  app.post("/api/history/:id/reexecute", async (req, res) => {
    try {
      const { fetchHistoryById } = await import("./api-client");

      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ success: false, error: "Invalid ID" });
      }

      const historyItem = await fetchHistoryById(id);

      if (!historyItem) {
        return res.status(404).json({ success: false, error: "History item not found" });
      }

      res.json({
        success: true,
        prompt: historyItem.prompt,
        model: historyItem.model,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : "Failed to reexecute",
      });
    }
  });

  // Cache viewing route
  app.get("/api/cache", async (req, res) => {
    try {
      const { fetchCache } = await import("./api-client");

      const cache = await fetchCache();

      res.json({ success: true, cache });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : "Failed to fetch cache",
      });
    }
  });

  const httpServer = createServer(app);

  // Setup WebSocket server
  setupWebSocket(httpServer);

  return httpServer;
}
