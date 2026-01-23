import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { parseString } from "xml2js";
import { promisify } from "util";
import OpenAI from "openai";

const parseXml = promisify(parseString);

const openai = new OpenAI({
  apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
});

const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
const AVATAR_ID = "15141bd577c043cea1d58609abf55a74";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  // Get latest RSS item from mortgage news
  app.get(api.rss.getLatest.path, async (req, res) => {
    try {
      const response = await fetch("https://www.mortgagenewsdaily.com/rss/rates");
      const xmlText = await response.text();
      
      const result = await parseXml(xmlText) as any;
      const items = result?.rss?.channel?.[0]?.item;
      
      if (!items || items.length === 0) {
        return res.status(500).json({ message: "No items found in RSS feed" });
      }
      
      const latestItem = items[0];
      const rssItem = {
        title: latestItem.title?.[0] || "",
        description: latestItem.description?.[0] || "",
        link: latestItem.link?.[0] || "",
        pubDate: latestItem.pubDate?.[0] || "",
      };
      
      res.json(rssItem);
    } catch (error) {
      console.error("Error fetching RSS:", error);
      res.status(500).json({ message: "Failed to fetch RSS feed" });
    }
  });

  // Rephrase content as marketing material using AI
  app.post(api.rss.rephrase.path, async (req, res) => {
    try {
      const input = api.rss.rephrase.input.parse(req.body);
      
      const prompt = `You are a marketing expert for the real estate and mortgage industry. 
Take the following mortgage rate news and rephrase it as an engaging, strategic marketing message specifically targeting first-time home buyers and refinancers.

Focus on:
- How current rates affect first-time buyers looking to purchase their first home
- Opportunities for homeowners considering refinancing their existing mortgage
- Clear, actionable next steps they should consider
- Creating urgency while remaining professional and trustworthy

Make it compelling, actionable, and professional. Keep it concise (under 200 words) and suitable for a video script that will be spoken by an AI avatar.

Title: ${input.title}
Description: ${input.description}

Write the marketing script that can be spoken directly. Do not include any stage directions or formatting - just the spoken words.`;

      const completion = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [{ role: "user", content: prompt }],
        max_completion_tokens: 500,
      });

      const marketingScript = completion.choices[0]?.message?.content || "";
      
      res.json({ marketingScript });
    } catch (error) {
      console.error("Error rephrasing content:", error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors[0].message });
      }
      res.status(500).json({ message: "Failed to rephrase content" });
    }
  });

  // Get all videos
  app.get(api.videos.list.path, async (req, res) => {
    try {
      const videosList = await storage.getVideos();
      res.json(videosList);
    } catch (error) {
      console.error("Error fetching videos:", error);
      res.status(500).json({ message: "Failed to fetch videos" });
    }
  });

  // Create a new video using HeyGen API
  app.post(api.videos.create.path, async (req, res) => {
    try {
      const input = api.videos.create.input.parse(req.body);
      
      const payload = {
        caption: false,
        video_inputs: [
          {
            character: {
              type: "avatar",
              avatar_id: AVATAR_ID,
              scale: 1,
              avatar_style: "normal",
              talking_style: "stable",
            },
            voice: {
              type: "text",
              input_text: input.marketingScript,
              voice_id: "2d5b0e6cf36f460aa7fc47e3eee4ba54",
              speed: 1.0,
              pitch: 0,
            },
            background: {
              type: "color",
              value: "#FFFFFF",
              play_style: "freeze",
              fit: "cover",
            },
          },
        ],
        dimension: {
          width: 1280,
          height: 720,
        },
      };

      const heygenResponse = await fetch("https://api.heygen.com/v2/video/generate", {
        method: "POST",
        headers: {
          "accept": "application/json",
          "content-type": "application/json",
          "x-api-key": HEYGEN_API_KEY || "",
        },
        body: JSON.stringify(payload),
      });

      const heygenData = await heygenResponse.json() as any;
      
      if (heygenData.error || !heygenData.data?.video_id) {
        console.error("HeyGen error:", heygenData);
        return res.status(500).json({ message: heygenData.error?.message || "Failed to generate video" });
      }

      const video = await storage.createVideo({
        videoId: heygenData.data.video_id,
        status: "pending",
        videoUrl: null,
        thumbnailUrl: null,
        originalTitle: input.originalTitle,
        originalDescription: input.originalDescription,
        marketingScript: input.marketingScript,
      });

      res.status(201).json(video);
    } catch (error) {
      console.error("Error creating video:", error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors[0].message });
      }
      res.status(500).json({ message: "Failed to create video" });
    }
  });

  // Get video status from HeyGen
  app.get(api.videos.getStatus.path, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const video = await storage.getVideo(id);
      
      if (!video) {
        return res.status(404).json({ message: "Video not found" });
      }

      // If already completed, return cached data
      if (video.status === "completed" && video.videoUrl) {
        return res.json({
          status: video.status,
          videoUrl: video.videoUrl,
          thumbnailUrl: video.thumbnailUrl,
        });
      }

      // Check HeyGen status
      const heygenResponse = await fetch(
        `https://api.heygen.com/v1/video_status.get?video_id=${video.videoId}`,
        {
          method: "GET",
          headers: {
            "accept": "application/json",
            "x-api-key": HEYGEN_API_KEY || "",
          },
        }
      );

      const heygenData = await heygenResponse.json() as any;
      
      let status = video.status;
      let videoUrl = video.videoUrl;
      let thumbnailUrl = video.thumbnailUrl;

      if (heygenData.data) {
        status = heygenData.data.status || "pending";
        
        if (status === "completed") {
          videoUrl = heygenData.data.video_url || null;
          thumbnailUrl = heygenData.data.thumbnail_url || null;
          
          // Update in database
          await storage.updateVideo(id, {
            status: "completed",
            videoUrl,
            thumbnailUrl,
          });
        } else if (status === "failed") {
          await storage.updateVideo(id, { status: "failed" });
        } else if (status === "processing") {
          await storage.updateVideo(id, { status: "processing" });
        }
      }

      res.json({
        status,
        videoUrl,
        thumbnailUrl,
      });
    } catch (error) {
      console.error("Error checking video status:", error);
      res.status(500).json({ message: "Failed to check video status" });
    }
  });

  return httpServer;
}
