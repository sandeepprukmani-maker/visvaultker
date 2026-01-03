import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  app.post(api.quotes.generate.path, async (req, res) => {
    try {
      const { postId } = api.quotes.generate.input.parse(req.body);

      const response = await fetch("https://4e503c11-74ac-465d-8d48-0544ffce9114-00-11zyexdimp3pe.janeway.replit.dev/api/posters", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ postId }),
      });

      const data = await response.json().catch(() => null);
      
      console.log("API response status:", response.status);
      console.log("API response data:", data);

      if (!response.ok) {
        console.error(`External API error: ${response.status} ${response.statusText}`, data);
        throw new Error(`External API error: ${response.statusText}`);
      }

      let caption = "";
      let author = "";

      if (data && typeof data === 'object') {
        if ('caption' in data) caption = String(data.caption);
        if ('author' in data) author = String(data.author);
        else if ('text' in data) caption = String(data.text);
        else if ('content' in data) caption = String(data.content);
        else if ('quote' in data) caption = String(data.quote);
      } else if (typeof data === 'string') {
        caption = data;
      }

      const quote = await storage.createQuote({
        caption,
        author: author || "Unknown",
        postId
      });

      res.status(201).json(quote);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join('.'),
        });
      }
      console.error("Error generating quote:", err);
      res.status(500).json({ message: "Failed to generate quote" });
    }
  });

  app.get(api.quotes.list.path, async (req, res) => {
    const quotes = await storage.getQuotes();
    res.json(quotes);
  });

  return httpServer;
}
