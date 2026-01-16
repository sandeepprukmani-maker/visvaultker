import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { runAutomation } from "./stagehand";
import { z } from "zod";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // === AUTOMATION ROUTES ===

  app.get(api.automations.list.path, async (req, res) => {
    const automations = await storage.listAutomations();
    res.json(automations);
  });

  app.post(api.automations.create.path, async (req, res) => {
    try {
      const input = api.automations.create.input.parse(req.body);
      const automation = await storage.createAutomation(input);
      
      // Update status to running and log start
      await storage.updateAutomation(automation.id, { status: "running" });

      // Start automation in background (don't await)
      runAutomation(automation.id, automation.prompt).catch(err => {
        console.error("Background automation error:", err);
      });
      
      res.status(201).json(automation);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join('.'),
        });
      }
      throw err;
    }
  });

  app.get(api.automations.get.path, async (req, res) => {
    const id = parseInt(req.params.id);
    const automation = await storage.getAutomation(id);
    if (!automation) {
      return res.status(404).json({ message: "Automation not found" });
    }
    const logs = await storage.getLogs(id);
    res.json({ ...automation, logs });
  });

  app.get(api.automations.logs.path, async (req, res) => {
    const id = parseInt(req.params.id);
    const logs = await storage.getLogs(id);
    res.json(logs);
  });

  return httpServer;
}
