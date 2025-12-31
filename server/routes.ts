import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { fetchLatestRateNews } from "./lib/rss";
import { openai } from "./replit_integrations/image/client"; // Use the client from integration
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

      // 1. Generate Catchy Caption (Text)
      const completion = await openai.chat.completions.create({
        model: "gpt-5.1",
        messages: [
          {
            role: "system",
            content: "You are a social media marketing expert for a mortgage company. Create a catchy, borrower-focused caption for Instagram/LinkedIn based on the provided news snippet. Focus on homebuyers and refinancing. Use emojis. Keep it under 280 characters."
          },
          {
            role: "user",
            content: `News Title: ${targetPost.title}\nSummary: ${targetPost.content}`
          }
        ],
      });
      
      const caption = completion.choices[0]?.message?.content || "Check out the latest mortgage rates!";

      // 2. Generate Image
      const imagePrompt = `Professional social media poster background for mortgage news. Theme: Finance, Home, Growth. Text overlay style (but do not add text): "Mortgage Rates Update". Abstract, modern, clean, blue and white color scheme. High quality.`;
      
      const imageResponse = await openai.images.generate({
        model: "gpt-image-1",
        prompt: imagePrompt,
        size: "1024x1024",
      });
      
      const b64_json = imageResponse.data[0]?.b64_json;

      if (!b64_json) {
        throw new Error("Failed to generate image");
      }

      // Convert base64 to data URL
      const imageUrl = `data:image/png;base64,${b64_json}`;

      // 3. Save Poster
      const poster = await storage.createPoster({
        postId: postId,
        imageUrl: imageUrl,
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

  // GET /api/posters/:id/download - Download poster image
  app.get("/api/posters/:id/download", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const poster = await storage.getPoster(id);
      
      if (!poster) {
        return res.status(404).json({ message: "Poster not found" });
      }

      // Extract base64 from data URL
      const base64Match = poster.imageUrl.match(/base64,(.+)$/);
      const base64Data = base64Match ? base64Match[1] : poster.imageUrl;
      
      const buffer = Buffer.from(base64Data, 'base64');
      res.setHeader('Content-Type', 'image/png');
      res.setHeader('Content-Disposition', 'attachment; filename="mortgage-poster.png"');
      res.send(buffer);
    } catch (error) {
      console.error("Error downloading poster:", error);
      res.status(500).json({ message: "Failed to download poster" });
    }
  });

  return httpServer;
}
