import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { WebSocketServer, WebSocket } from "ws";
import { executeAutomation, type StepData } from "./eko-agent";
import { insertAutomationJobSchema } from "@shared/schema";
import { log } from "./index";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  const wss = new WebSocketServer({ server: httpServer, path: "/api/ws" });

  wss.on("connection", (ws: WebSocket) => {
    log("WebSocket client connected", "websocket");

    ws.on("message", async (message: string) => {
      try {
        const data = JSON.parse(message.toString());
        
        if (data.type === "execute") {
          const { prompt } = data;
          
          const job = await storage.createJob({
            prompt,
            status: "running",
            steps: [],
          });

          ws.send(JSON.stringify({ type: "job_started", jobId: job.id }));

          const steps: StepData[] = [];

          const result = await executeAutomation(prompt, (step: StepData) => {
            steps.push(step);
            ws.send(JSON.stringify({ type: "step", step }));
          });

          await storage.updateJob(job.id, {
            status: result.success ? "completed" : "failed",
            steps,
            result: result.result,
            error: result.error,
            completedAt: new Date(),
          });

          ws.send(JSON.stringify({ 
            type: "job_completed", 
            jobId: job.id,
            success: result.success,
            result: result.result,
            error: result.error,
          }));
        }
      } catch (error: any) {
        log(`WebSocket error: ${error.message}`, "websocket");
        ws.send(JSON.stringify({ type: "error", message: error.message }));
      }
    });

    ws.on("close", () => {
      log("WebSocket client disconnected", "websocket");
    });
  });

  app.get("/api/jobs", async (_req, res) => {
    try {
      const jobs = await storage.listJobs();
      res.json(jobs);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/jobs/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const job = await storage.getJob(id);
      if (!job) {
        return res.status(404).json({ error: "Job not found" });
      }
      res.json(job);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  return httpServer;
}
