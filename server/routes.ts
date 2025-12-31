import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { fetchLatestRateNews, fetchCurrentRates } from "./lib/rss";
import { getOpenAI } from "./replit_integrations/image/client";
import { api } from "@shared/routes";
import { z } from "zod";

// Import integration routes
import { registerChatRoutes } from "./replit_integrations/chat";
import { registerImageRoutes } from "./replit_integrations/image";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Register integration routes
  registerChatRoutes(app);
  registerImageRoutes(app);

  // --- API Routes ---

  // GET /api/posts/latest
  app.get(api.posts.latest.path, async (req, res) => {
    try {
      // 1. Fetch from RSS
      const latestRssItem = await fetchLatestRateNews();
      
      if (!latestRssItem) {
        // Fallback to DB if RSS fails
        const latestDb = await storage.getLatestPost();
        if (!latestDb) {
            return res.status(500).json({ message: "Could not fetch news" });
        }
        return res.json(latestDb);
      }

      // 2. Check if exists in DB
      let post = await storage.getPostByGuid(latestRssItem.guid || latestRssItem.link || 'unknown');

      if (!post) {
        // 3. Insert if new
        post = await storage.createPost({
          title: latestRssItem.title || "No Title",
          link: latestRssItem.link || "",
          content: latestRssItem.contentSnippet || latestRssItem.content || "",
          pubDate: latestRssItem.pubDate || new Date().toISOString(),
          guid: latestRssItem.guid || latestRssItem.link || 'unknown',
        });
      }

      res.json(post);
    } catch (error) {
      console.error("Error in /api/posts/latest:", error);
      res.status(500).json({ message: "Internal Server Error" });
    }
  });

  // GET /api/posts
  app.get(api.posts.list.path, async (req, res) => {
    const posts = await storage.getAllPosts();
    res.json(posts);
  });

  // POST /api/posters
  app.post(api.posters.create.path, async (req, res) => {
    try {
      const { postId } = api.posters.create.input.parse(req.body);
      const post = await storage.getPostByGuid(String(postId)); // Wait, postId is ID (int) or GUID?
      // Schema says postId is int references posts.id.
      // But I need to fetch the post first. I need getPostById.
      // Let's add getPostById to storage or just use what we have?
      // storage.getAllPosts() and find? No, inefficient.
      // I'll assume I can add getPost(id) to storage or just rely on the frontend passing the right ID.
      // Wait, storage.ts didn't have getPost(id). I'll add it or work around.
      // I'll add `getPost(id)` to storage in a moment. 
      // For now, let's filter from getAllPosts (temporary hack) or use query builder.
      
      // Let's modify storage first? No, I am in one batch.
      // I will implement a quick fix here or assume storage has it.
      // I defined `getLatestPost`, `getPostByGuid`, `getAllPosts`.
      // I need `getPost(id)`.
      
      // Okay, let's look at `server/storage.ts` I just wrote. 
      // It DOES NOT have getPost(id).
      // I will create a query here directly or update storage in next turn?
      // I can't update storage in same turn easily if I already sent the write command?
      // Actually I sent `server/storage.ts` in THIS batch. I can edit the content string before I send it!
      // I will update the `server/storage.ts` content in this tool call to include `getPost`.

      // See below for updated `server/storage.ts` content.

      // Back to logic:
      const targetPost = await storage.getPost(postId);
      if (!targetPost) {
        return res.status(404).json({ message: "Post not found" });
      }

      // 0. Fetch current market rates
      const currentRates = await fetchCurrentRates();

      // 1. Generate Catchy Caption (Text)
      let openai;
      try {
        openai = getOpenAI();
      } catch (e) {
        return res.status(400).json({ 
          message: "AI not configured. Please click the 'Setup AI' button in the Replit interface to enable content generation." 
        });
      }

      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: "You are a social media marketing expert for a mortgage company. Create a very short, catchy, and positive Instagram caption. Analyze the news with a focus on opportunities for homebuyers and refinancers, avoiding any panic-inducing language. Weave in current market rates contextually. Max 150 characters. Use 1 emoji."
          },
          {
            role: "user",
            content: `News Article: "${targetPost.title}"\nContext: ${targetPost.content}\n\nCurrent Rates: ${currentRates}`
          }
        ],
      });
      
      const caption = completion.choices[0]?.message?.content || "Check out the latest mortgage rates!";

      // 2. Generate Caption only (No Image)
      // The caption generation is already handled above in step 1 logic.
      // We just need to save it.

      // 3. Save Caption (Still using posters table for now but with empty image)
      const poster = await storage.createPoster({
        postId: postId,
        caption: caption,
      });

      res.status(201).json(poster);

    } catch (error) {
      console.error("Error creating poster:", error);
      res.status(500).json({ message: "Failed to create poster" });
    }
  });

  // GET /api/posters
  app.get(api.posters.list.path, async (req, res) => {
    const items = await storage.getPosters();
    res.json(items);
  });

  // GET /api/posters/:id/download - Download poster content
  app.get("/api/posters/:id/download", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const poster = await storage.getPoster(id);
      
      if (!poster) {
        return res.status(404).json({ message: "Poster not found" });
      }

      res.setHeader('Content-Type', 'text/plain');
      res.setHeader('Content-Disposition', `attachment; filename="caption-${id}.txt"`);
      res.send(poster.caption);
    } catch (error) {
      console.error("Error downloading poster:", error);
      res.status(500).json({ message: "Failed to download poster" });
    }
  });

  return httpServer;
}
