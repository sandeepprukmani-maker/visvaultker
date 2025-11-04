import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  app.use("/api/python", async (req, res) => {
    try {
      const pythonUrl = `http://localhost:8000${req.url}`;
      const response = await fetch(pythonUrl, {
        method: req.method,
        headers: {
          "Content-Type": "application/json",
        },
        body: req.method !== "GET" && req.method !== "HEAD" ? JSON.stringify(req.body) : undefined,
      });
      
      const data = await response.json();
      res.status(response.status).json(data);
    } catch (error) {
      res.status(500).json({ error: "Python backend unavailable" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
