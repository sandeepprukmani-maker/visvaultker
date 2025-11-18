import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { AutomationExecutor, type AutomationModel } from "./automation";
import { insertAutomationSchema, insertSettingsSchema } from "@shared/schema";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time updates
  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });
  
  // Track active executors for cleanup
  const activeExecutors = new Map<WebSocket, AutomationExecutor>();

  wss.on("connection", (ws: WebSocket) => {
    console.log("WebSocket client connected");

    ws.on("message", async (message: string) => {
      try {
        const data = JSON.parse(message.toString());
        
        // Handle different message types
        if (data.type === "execute_automation") {
          // Validate payload
          const executeSchema = z.object({
            type: z.literal("execute_automation"),
            prompt: z.string().min(1),
            model: z.enum(["openai", "anthropic", "gemini"]),
          });
          
          const validated = executeSchema.parse(data);
          const { prompt, model } = validated;
          
          // Send execution started event
          ws.send(JSON.stringify({
            type: "execution_started",
            data: { prompt },
          }));

          // Get automation mode from settings
          const settings = await storage.getSettings();
          const automationMode = settings?.automationMode || "act";

          // Create automation record
          const automation = await storage.createAutomation({
            prompt,
            status: "running",
            model,
            result: null,
            logs: null,
            error: null,
            duration: null,
          });

          // Execute automation
          const executor = new AutomationExecutor(ws);
          activeExecutors.set(ws, executor);
          
          try {
            await executor.initialize(model as AutomationModel);
            
            // Execute using the selected automation mode
            const result = automationMode === "agent" 
              ? await executor.executeAgent(prompt, model as AutomationModel)
              : await executor.execute(prompt);

            // Update automation with result
            await storage.updateAutomation(automation.id, {
              status: result.success ? "success" : "error",
              result: result.result,
              error: result.error,
              logs: result.logs as any,
              duration: result.duration,
            });

            // Send completion event
            ws.send(JSON.stringify({
              type: "execution_completed",
              data: {
                automationId: automation.id,
                result: result.result,
                duration: result.duration,
                logs: result.logs,
              },
            }));
          } catch (error: any) {
            // Update automation with error
            await storage.updateAutomation(automation.id, {
              status: "error",
              error: error.message,
              logs: executor.getLogs() as any,
            });

            // Send error event
            ws.send(JSON.stringify({
              type: "execution_error",
              data: {
                automationId: automation.id,
                error: error.message,
              },
            }));
          } finally {
            await executor.cleanup();
            activeExecutors.delete(ws);
          }
        } else {
          // Ignore unknown message types (for future extensibility)
          console.log("Unknown WebSocket message type:", data.type);
        }
      } catch (error: any) {
        console.error("WebSocket message handling error:", error);
        
        // Send error to client if validation fails
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: "execution_error",
            data: {
              automationId: "",
              error: error.message || "Invalid request",
            },
          }));
        }
      }
    });

    ws.on("close", async () => {
      console.log("WebSocket client disconnected");
      
      // Cleanup any active automation for this connection
      const executor = activeExecutors.get(ws);
      if (executor) {
        console.log("Cleaning up executor for disconnected client");
        await executor.cleanup();
        activeExecutors.delete(ws);
      }
    });

    ws.on("error", (error) => {
      console.error("WebSocket connection error:", error);
    });
  });

  // Get all automations (history)
  app.get("/api/automations", async (req, res) => {
    try {
      const automations = await storage.getAllAutomations();
      res.json(automations);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get single automation
  app.get("/api/automations/:id", async (req, res) => {
    try {
      const automation = await storage.getAutomation(req.params.id);
      if (!automation) {
        return res.status(404).json({ error: "Automation not found" });
      }
      res.json(automation);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Delete automation
  app.delete("/api/automations/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteAutomation(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Automation not found" });
      }
      res.json({ success: true });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get all cached patterns
  app.get("/api/cache", async (req, res) => {
    try {
      const cache = await storage.getAllCachedPatterns();
      res.json(cache);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Get settings
  app.get("/api/settings", async (req, res) => {
    try {
      const settings = await storage.getSettings();
      res.json(settings);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Update settings
  app.patch("/api/settings", async (req, res) => {
    try {
      // Create a partial schema for settings updates
      const updateSettingsSchema = insertSettingsSchema.partial();
      const validated = updateSettingsSchema.parse(req.body);
      
      const settings = await storage.updateSettings(validated);
      res.json(settings);
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: "Invalid settings data", details: error.errors });
      } else {
        res.status(500).json({ error: error.message });
      }
    }
  });

  return httpServer;
}
