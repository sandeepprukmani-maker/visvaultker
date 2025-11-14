import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { convertPromptToPlaywrightActions } from "./gemini";
import { playwrightExecutor } from "./playwright-executor";
import { randomUUID } from "crypto";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time automation updates
  // Using distinct path to avoid conflict with Vite's HMR websocket
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  // Track active WebSocket connections
  const connections = new Map<string, WebSocket>();

  wss.on('connection', (ws: WebSocket) => {
    const connectionId = randomUUID();
    connections.set(connectionId, ws);

    console.log(`WebSocket client connected: ${connectionId}`);

    ws.on('close', () => {
      connections.delete(connectionId);
      console.log(`WebSocket client disconnected: ${connectionId}`);
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  // Broadcast message to all connected clients
  function broadcast(message: any) {
    const data = JSON.stringify(message);
    connections.forEach((ws) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });
  }

  // API Routes

  // Execute automation from natural language prompt
  app.post("/api/execute", async (req, res) => {
    try {
      const { prompt } = req.body;
      
      if (!prompt || typeof prompt !== 'string') {
        return res.status(400).json({ error: "Prompt is required" });
      }

      const executionId = randomUUID();
      const startTime = Date.now();

      // Send start notification via WebSocket
      broadcast({
        type: "automation_start",
        data: { prompt, executionId },
      });

      // Step 1: Convert prompt to Playwright actions using Gemini
      broadcast({
        type: "automation_progress",
        data: { executionId, step: "Converting prompt to Playwright actions..." },
      });

      const plan = await convertPromptToPlaywrightActions(prompt);
      const tokensUsed = plan.estimatedTokens;

      // Step 2: Execute Playwright actions
      broadcast({
        type: "automation_progress",
        data: { executionId, step: "Executing browser automation..." },
      });

      const result = await playwrightExecutor.executeMultipleActions(plan.actions);
      const executionTime = Date.now() - startTime;

      if (!result.success) {
        // Send error notification
        broadcast({
          type: "automation_error",
          data: { executionId, error: result.error || "Execution failed" },
        });

        // Still save to history even if failed
        await storage.createAutomationHistory({
          prompt,
          executedCode: result.executedCode,
          pageState: result.pageState,
          result: result.error || "Execution failed",
          status: "error",
          tokensUsed,
          executionTime,
        });

        return res.status(500).json({
          executionId,
          success: false,
          error: result.error,
        });
      }

      // Save successful execution to history
      const historyEntry = await storage.createAutomationHistory({
        prompt,
        executedCode: result.executedCode,
        pageState: result.pageState,
        result: result.result,
        status: "success",
        tokensUsed,
        executionTime,
      });

      // Send completion notification via WebSocket
      broadcast({
        type: "automation_complete",
        data: {
          executionId,
          result: result.result,
          executedCode: result.executedCode,
          pageState: result.pageState,
          tokensUsed,
          executionTime,
        },
      });

      res.json({
        executionId,
        success: true,
        historyId: historyEntry.id,
      });
    } catch (error) {
      console.error("Execution error:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Internal server error",
      });
    }
  });

  // Get automation history
  app.get("/api/history", async (req, res) => {
    try {
      const history = await storage.getAllAutomationHistory();
      res.json(history);
    } catch (error) {
      console.error("Error fetching history:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Internal server error",
      });
    }
  });

  // Get single history item
  app.get("/api/history/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const history = await storage.getAutomationHistory(id);
      
      if (!history) {
        return res.status(404).json({ error: "History not found" });
      }
      
      res.json(history);
    } catch (error) {
      console.error("Error fetching history item:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Internal server error",
      });
    }
  });

  // Get all templates
  app.get("/api/templates", async (req, res) => {
    try {
      const templates = await storage.getAllTemplates();
      res.json(templates);
    } catch (error) {
      console.error("Error fetching templates:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Internal server error",
      });
    }
  });

  // Get token metrics
  app.get("/api/metrics", async (req, res) => {
    try {
      const metrics = await storage.getTokenMetrics();
      res.json(metrics);
    } catch (error) {
      console.error("Error fetching metrics:", error);
      res.status(500).json({
        error: error instanceof Error ? error.message : "Internal server error",
      });
    }
  });

  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  return httpServer;
}
