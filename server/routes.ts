import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { insertTaskSchema } from "@shared/schema";
import { executeAutomation } from "./automation-executor";
import { initMcpClient, getConnectionStatus } from "./mcp-client";
import { z } from "zod";

const clients = new Set<WebSocket>();

function broadcast(message: object) {
  const data = JSON.stringify(message);
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });

  wss.on("connection", (ws) => {
    clients.add(ws);
    console.log("WebSocket client connected");

    ws.send(
      JSON.stringify({
        type: "connection_status",
        status: getConnectionStatus(),
      })
    );

    ws.on("close", () => {
      clients.delete(ws);
      console.log("WebSocket client disconnected");
    });

    ws.on("error", (error) => {
      console.error("WebSocket error:", error);
      clients.delete(ws);
    });
  });

  initMcpClient()
    .then(() => {
      broadcast({ type: "connection_status", status: "connected" });
    })
    .catch((error) => {
      console.error("Failed to initialize MCP client:", error);
      broadcast({ type: "connection_status", status: "disconnected" });
    });

  app.get("/api/tasks", async (_req, res) => {
    try {
      const tasks = await storage.getAllTasks();
      res.json(tasks);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      res.status(500).json({ error: "Failed to fetch tasks" });
    }
  });

  app.get("/api/tasks/:id", async (req, res) => {
    try {
      const task = await storage.getTask(req.params.id);
      if (!task) {
        return res.status(404).json({ error: "Task not found" });
      }
      res.json(task);
    } catch (error) {
      console.error("Error fetching task:", error);
      res.status(500).json({ error: "Failed to fetch task" });
    }
  });

  app.post("/api/execute", async (req, res) => {
    try {
      const parseResult = insertTaskSchema.safeParse(req.body);
      if (!parseResult.success) {
        return res.status(400).json({ 
          error: "Invalid request", 
          details: parseResult.error.errors 
        });
      }

      const { prompt } = parseResult.data;
      const task = await storage.createTask(prompt);

      broadcast({ type: "task_update", task });

      executeAutomation(task.id, prompt, broadcast).catch((error) => {
        console.error("Automation execution error:", error);
      });

      res.json(task);
    } catch (error) {
      console.error("Error creating task:", error);
      res.status(500).json({ error: "Failed to create task" });
    }
  });

  app.delete("/api/tasks", async (_req, res) => {
    try {
      await storage.clearTasks();
      res.json({ success: true });
    } catch (error) {
      console.error("Error clearing tasks:", error);
      res.status(500).json({ error: "Failed to clear tasks" });
    }
  });

  app.get("/api/status", async (_req, res) => {
    res.json({
      mcpStatus: getConnectionStatus(),
    });
  });

  return httpServer;
}
