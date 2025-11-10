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
import { StagehandStep, emitLocatorScript, normalizeStep } from "./locator-generator";

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

        // Navigate to URL
        addLog(`Navigating to ${validatedData.url}`, "running");
        await stagehand.page.goto(validatedData.url, { waitUntil: "networkidle" });
        addLog(`Loaded ${validatedData.url}`, "success");

        let result: any;
        let generatedCode = "";

        // Execute based on mode
        switch (validatedData.mode) {
          case "act":
            addLog(`Executing action: ${validatedData.prompt}`, "running");
            // stagehand.page is a live proxy that automatically follows new tabs/popups
            result = await stagehand.page.act(validatedData.prompt);
            addLog("Action completed", "success", undefined, "Element interacted successfully");

            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();

// Use stagehand.page directly - it's a live proxy that follows new tabs/popups
await stagehand.page.goto("${validatedData.url}");
await stagehand.page.act("${validatedData.prompt}");

await stagehand.close();`;
            break;

          case "observe":
            addLog(`Observing: ${validatedData.prompt}`, "running");
            result = await stagehand.page.observe(validatedData.prompt);
            addLog("Observation completed", "success", undefined, JSON.stringify(result, null, 2));

            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();

// Use stagehand.page directly - it's a live proxy that follows new tabs/popups
await stagehand.page.goto("${validatedData.url}");
const result = await stagehand.page.observe("${validatedData.prompt}");
console.log("Observed:", result);

await stagehand.close();`;
            break;

          case "extract":
            addLog(`Extracting: ${validatedData.prompt}`, "running");
            // For extract, we need a schema - use a generic one for demo
            const extractSchema = z.object({
              data: z.string().describe(validatedData.prompt)
            });
            result = await stagehand.page.extract({
              instruction: validatedData.prompt,
              schema: extractSchema
            });
            addLog("Extraction completed", "success", undefined, JSON.stringify(result, null, 2));

            generatedCode = `import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";

const stagehand = new Stagehand({
  env: "LOCAL",
  modelName: "${validatedData.model}",
  enableCaching: true
});

await stagehand.init();

// Use stagehand.page directly - it's a live proxy that follows new tabs/popups
await stagehand.page.goto("${validatedData.url}");

const schema = z.object({
  data: z.string().describe("${validatedData.prompt}")
});

const result = await stagehand.page.extract({
  instruction: "${validatedData.prompt}",
  schema: schema
});
console.log("Extracted:", result);

await stagehand.close();`;
            break;

          case "agent":
            addLog(`Running agent: ${validatedData.prompt}`, "running");
            const agent = stagehand.agent({
              model: validatedData.model,
              instructions: "You're a helpful assistant that can control a web browser.",
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

// Use stagehand.page directly - it's a live proxy that follows new tabs/popups
await stagehand.page.goto("${validatedData.url}");

const agent = stagehand.agent({
  model: "${validatedData.model}",
  instructions: "You're a helpful assistant that can control a web browser.",
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

        const capturedSteps: StagehandStep[] = [];

        // Navigate to URL
        addLog(`Navigating to ${parsedPrompt.url}`, "running");
        await stagehand.page.goto(parsedPrompt.url, { waitUntil: "networkidle" });
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
              observeResults = await stagehand.page.observe(parsedPrompt.task);
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
                  const locator = stagehand.page.locator(firstResult.selector);
                  await locator.highlight();
                  await stagehand.page.waitForTimeout(1000); // Wait to show highlight
                  addLog("Element highlighted", "success", firstResult.selector);
                }
              } catch (highlightError) {
                console.log("Could not highlight element:", highlightError);
              }

              // Act on the observed element
              addLog(`Executing action: ${parsedPrompt.task}`, "running");
              result = await stagehand.page.act(firstResult);
              addLog("Action completed", "success", undefined, "Element interacted successfully");
            } else {
              // Fallback to direct act if observe fails
              addLog(`Executing action directly: ${parsedPrompt.task}`, "running");
              result = await stagehand.page.act(parsedPrompt.task);

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
            result = await stagehand.page.observe(parsedPrompt.task);

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
                    const locator = stagehand.page.locator(obs.selector);
                    await locator.highlight();
                    await stagehand.page.waitForTimeout(1500); // Wait to show highlight
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
            result = await stagehand.page.extract({
              instruction: parsedPrompt.task,
              schema: extractSchema
            });

            // Capture extract step (doesn't have specific selectors, but note the action)
            capturedSteps.push({
              action: "extract",
              description: parsedPrompt.task,
            });

            addLog("Extraction completed", "success", undefined, JSON.stringify(result, null, 2));
            break;

          case "agent":
            addLog(`Running agent: ${parsedPrompt.task}`, "running");
            const agent = stagehand.agent({
              model: validatedData.model,
              instructions: "You're a helpful automation assistant that can control a web browser.",
            });
            result = await agent.execute(parsedPrompt.task);

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
          const screenshotBuffer = await stagehand.page.screenshot({
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

  const httpServer = createServer(app);

  // Setup WebSocket server
  setupWebSocket(httpServer);

  return httpServer;
}
