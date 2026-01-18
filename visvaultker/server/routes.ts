import OpenAI from "openai";
import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { db } from "./db";
import { posters, videos } from "@shared/schema";
import { eq, desc } from "drizzle-orm";
import { fetchLatestRateNews, fetchCurrentRates } from "./lib/rss";
import { openai as openaiClient } from "./replit_integrations/image/client";
import { api } from "@shared/routes";
import { z } from "zod";

import { registerChatRoutes } from "./replit_integrations/chat";
import { registerAudioRoutes } from "./replit_integrations/audio";
import { registerImageRoutes } from "./replit_integrations/image";

const openai = new OpenAI({
  apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  registerChatRoutes(app);
  registerAudioRoutes(app);
  registerImageRoutes(app);

  app.get(api.posts.latest.path, async (req, res) => {
    try {
      const latestRssItem = await fetchLatestRateNews();
      if (!latestRssItem) {
        const latestDb = await storage.getLatestPost();
        if (!latestDb) return res.status(500).json({ message: "Could not fetch news" });
        return res.json(latestDb);
      }
      let post = await storage.getPostByGuid(latestRssItem.guid || latestRssItem.link || "unknown");
      if (!post) {
        post = await storage.createPost({
          title: latestRssItem.title || "Untitled Market Update",
          link: latestRssItem.link || "#",
          content: latestRssItem.contentSnippet || latestRssItem.content || "",
          pubDate: latestRssItem.pubDate || new Date().toISOString(),
          guid: latestRssItem.guid || latestRssItem.link || Math.random().toString(36).substring(7),
        });
      }
      res.json(post);
    } catch (error: any) {
      const latestDb = await storage.getLatestPost();
      if (latestDb) return res.json(latestDb);
      res.status(500).json({ error: error.message });
    }
  });

  app.get(api.posts.list.path, async (req, res) => {
    try {
      const posts = await storage.getAllPosts();
      res.json(posts);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post(api.posters.create.path, async (req, res) => {
    try {
      const { postId } = req.body;
      const post = await storage.getPost(postId);
      if (!post) return res.status(404).json({ message: "Post not found" });
      const completion = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          { role: "system", content: "You are a mortgage marketing expert. Generate a viral social media caption." },
          { role: "user", content: post.content || post.title }
        ]
      });
      const caption = completion.choices[0].message.content || "Market update!";
      const rates = await fetchCurrentRates();
      const htmlContent = "<div>Flyer Content</div>";
      const poster = await storage.createPoster({ postId, caption, htmlContent });
      res.json(poster);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get(api.posters.list.path, async (req, res) => {
    try {
      const posters = await storage.getPosters();
      res.json(posters);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/generate-video", async (req, res) => {
    try {
      const { postId } = req.body;
      const post = await storage.getPost(parseInt(postId));
      if (!post) throw new Error("Post not found");
      const scriptResponse = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          { 
            role: "system", 
            content: "You are a mortgage marketing expert. Convert the following social media caption into a crisp, short, and punchy 30-second video script focusing on home buyers and refinancers. The person will be sitting and delivering the message directly. No stage directions, just the spoken text." 
          },
          { role: "user", content: post.content || post.title }
        ],
      });
      const script = scriptResponse.choices[0].message.content || "";
      const heygenResponse = await fetch("https://api.heygen.com/v2/video/generate", {
        method: "POST",
        headers: {
          "X-Api-Key": process.env.HEYGEN_API_KEY || "",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "Marketing Reel",
          dimension: { width: 720, height: 1280 },
          video_inputs: [{
            character: { type: "avatar", avatar_id: "2eca5f61117d4a708242cb27266ddc4a", scale: 1.15, offset: { x: 0, y: -0.05 } },
            voice: { type: "text", voice_id: "e273b0dcbaf34113b177056e311dc2d2", input_text: script },
            background: { type: "color", value: "#000000" }
          }]
        }),
      });
      if (!heygenResponse.ok) throw new Error(await heygenResponse.text());
      const heygenData = await heygenResponse.json();
      const [newVideo] = await db.insert(videos).values({
        postId: parseInt(postId),
        videoId: heygenData.data.video_id,
        status: "processing",
        script: script
      }).returning();
      res.json({ video_id: heygenData.data.video_id, script, id: newVideo.id });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/videos", async (req, res) => {
    try {
      const allVideos = await db.select().from(videos).orderBy(desc(videos.createdAt));
      res.json(allVideos);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/video-status/:id", async (req, res) => {
    try {
      console.log(`Polling HeyGen status for: ${req.params.id}`);
      const response = await fetch(`https://api.heygen.com/v2/video_status.get?video_id=${req.params.id}`, {
        headers: { 
          "X-Api-Key": process.env.HEYGEN_API_KEY || "",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        // HeyGen might return 404 if the video is still in a very early stage or being routed
        if (response.status === 404) {
          console.log(`Video ${req.params.id} not found yet, assuming processing...`);
          return res.json({ data: { status: "processing" } });
        }
        const errorText = await response.text();
        console.error(`HeyGen API Error (${response.status}):`, errorText);
        return res.status(response.status).json({ error: errorText });
      }

      const data = await response.json();
      console.log(`HeyGen Response for ${req.params.id}:`, JSON.stringify(data, null, 2));
      
      // Comprehensive extraction of status and URLs from multiple possible response structures
      const rawStatus = data.data?.status || data.status;
      const videoUrl = data.data?.video_url || data.video_url || data.data?.url || data.url;
      const thumbnailUrl = data.data?.thumbnail_url || data.thumbnail_url || data.data?.poster || data.poster;
      
      if (rawStatus) {
        const status = String(rawStatus).toLowerCase();
        let dbStatus = "processing";
        
        // Comprehensive status mapping based on observed API behavior across different versions
        const completedStates = ["completed", "success", "done", "processed", "finish", "finished", "succeeded"];
        const failedStates = ["failed", "error", "rejected", "fail", "canceled", "cancelled"];

        if (completedStates.includes(status)) {
          dbStatus = "completed";
        } else if (failedStates.includes(status)) {
          dbStatus = "failed";
        }
        
        console.log(`Mapping HeyGen status '${status}' to internal status '${dbStatus}' for ${req.params.id}`);

        // Update database with latest status and URLs
        // Ensure we capture videoUrl and thumbnailUrl if they exist in the response
        await db.update(videos).set({ 
          status: dbStatus, 
          videoUrl: videoUrl || null, 
          thumbnailUrl: thumbnailUrl || null 
        }).where(eq(videos.videoId, req.params.id));
      }
      res.json(data);
    } catch (error: any) {
      console.error(`Status Polling Exception for ${req.params.id}:`, error);
      res.status(500).json({ error: error.message });
    }
  });

  return httpServer;
}
