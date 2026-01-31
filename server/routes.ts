import express, { type Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { parseString } from "xml2js";
import { promisify } from "util";
import OpenAI from "openai";
import ffmpeg from "fluent-ffmpeg";
import path from "path";
import fs from "fs";
import multer from "multer";

const parseXml = promisify(parseString);

// Configure multer for banner uploads
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const dir = path.join(process.cwd(), "public", "banners");
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      cb(null, dir);
    },
    filename: (req, file, cb) => {
      cb(null, "current_banner.png"); // Always overwrite with same name for simplicity
    },
  }),
});

function getOpenAIClient(): OpenAI {
  if (!process.env.AI_INTEGRATIONS_OPENAI_API_KEY) {
    throw new Error("OpenAI API key not configured. Please set up AI integrations.");
  }
  return new OpenAI({
    apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
    baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
  });
}

const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
const AVATAR_ID = "15141bd577c043cea1d58609abf55a74";

async function deleteVideoFromHeyGen(videoId: string, apiKey: string): Promise<boolean> {
  try {
    const response = await fetch(`https://api.heygen.com/v1/video/${videoId}.delete`, {
      method: "DELETE",
      headers: {
        "x-api-key": apiKey,
      },
    });
    const data = await response.json() as any;
    if (response.ok) {
      console.log(`Successfully deleted video ${videoId} from HeyGen`);
      return true;
    } else {
      console.error(`Failed to delete video ${videoId} from HeyGen:`, data);
      return false;
    }
  } catch (error) {
    console.error(`Error deleting video ${videoId} from HeyGen:`, error);
    return false;
  }
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Static file serving for processed videos and banners
  const processedVideosPath = path.join(process.cwd(), "public", "processed_videos");
  if (!fs.existsSync(processedVideosPath)) {
    fs.mkdirSync(processedVideosPath, { recursive: true });
  }
  app.use("/processed_videos", express.static(processedVideosPath));
  app.use("/banners", express.static(path.join(process.cwd(), "public", "banners")));
  
  // Banner upload endpoint
  app.post("/api/banners/upload", upload.single("banner"), (req, res) => {
    if (!req.file) {
      return res.status(400).json({ message: "No file uploaded" });
    }
    res.json({ message: "Banner uploaded successfully", url: "/banners/current_banner.png" });
  });

  // API Key management
  app.get("/api/keys", async (req, res) => {
    const keys = await storage.getApiKeys("heygen");
    res.json(keys.map(k => ({ ...k, key: k.key.substring(0, 4) + "****" + k.key.substring(k.key.length - 4) })));
  });

  app.post("/api/keys", async (req, res) => {
    const { key } = req.body;
    if (!key) return res.status(400).json({ message: "Key is required" });
    const newKey = await storage.createApiKey({ key, service: "heygen", isActive: "true" });
    res.json(newKey);
  });

  app.delete("/api/keys/:id", async (req, res) => {
    await storage.deleteApiKey(parseInt(req.params.id));
    res.json({ message: "Key deleted" });
  });

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

IMPORTANT: Keep it SHORT and concise - approximately 60-65 words maximum. The spoken script must be around 25 seconds when read aloud (about 2.5 words per second). Do not exceed this length under any circumstances.

Title: ${input.title}
Description: ${input.description}

Write the marketing script that can be spoken directly. Do not include any stage directions or formatting - just the spoken words. Remember: maximum 65 words for a 25-second video.`;

      const completion = await getOpenAIClient().chat.completions.create({
        model: "gpt-4o",
        messages: [{ role: "user", content: prompt }],
        max_completion_tokens: 1000,
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
              voice_id: "D5e61LbU1mWzmUL9BtQZ",
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
          width: 720,
          height: 1280,
        },
      };

      // Try multiple API keys if one fails
      let lastError = null;

      // Try database-stored keys FIRST (prioritize UI-added keys)
      const dbKeys = await storage.getApiKeys("heygen");
      const activeKeys = dbKeys.filter(k => k.isActive === "true");

      for (const apiKey of activeKeys) {
        try {
          const heygenResponse = await fetch("https://api.heygen.com/v2/video/generate", {
            method: "POST",
            headers: {
              "accept": "application/json",
              "content-type": "application/json",
              "x-api-key": apiKey.key,
            },
            body: JSON.stringify(payload),
          });

          const heygenData = await heygenResponse.json() as any;
          
          if (!heygenData.error && heygenData.data?.video_id) {
            // Update last used time
            await storage.updateApiKey(apiKey.id, { lastUsedAt: new Date() });
            
            const video = await storage.createVideo({
              videoId: heygenData.data.video_id,
              status: "pending",
              videoUrl: null,
              thumbnailUrl: null,
              originalTitle: input.originalTitle,
              originalDescription: input.originalDescription,
              marketingScript: input.marketingScript,
            });
            return res.status(201).json(video);
          }

          // Mark key as potentially problematic if it's a specific "key" error
          if (heygenData.error?.code === 401 || heygenData.error?.message?.toLowerCase().includes("unauthorized")) {
             await storage.updateApiKey(apiKey.id, { isActive: "false" });
          }
          lastError = heygenData.error?.message || "API key failed";
        } catch (e: any) {
          lastError = e.message;
        }
      }

      // Finally try the configured secret as a last resort if it exists and no custom keys succeeded
      if (HEYGEN_API_KEY && activeKeys.length === 0) {
        try {
          const heygenResponse = await fetch("https://api.heygen.com/v2/video/generate", {
            method: "POST",
            headers: {
              "accept": "application/json",
              "content-type": "application/json",
              "x-api-key": HEYGEN_API_KEY,
            },
            body: JSON.stringify(payload),
          });

          const heygenData = await heygenResponse.json() as any;
          if (!heygenData.error && heygenData.data?.video_id) {
            const video = await storage.createVideo({
              videoId: heygenData.data.video_id,
              status: "pending",
              videoUrl: null,
              thumbnailUrl: null,
              originalTitle: input.originalTitle,
              originalDescription: input.originalDescription,
              marketingScript: input.marketingScript,
            });
            return res.status(201).json(video);
          }
          lastError = heygenData.error?.message || "Generation failed with primary key";
        } catch (e: any) {
          lastError = e.message;
        }
      }

      return res.status(500).json({ message: lastError || "All API keys failed" });
    } catch (error) {
      console.error("Error creating video:", error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: error.errors[0].message });
      }
      res.status(500).json({ message: "Failed to create video" });
    }
  });

  // Get video status from HeyGen
  app.get(api.videos.getStatus.path, async (req: any, res) => {
    try {
      const id = parseInt(req.params.id);
      const video = await storage.getVideo(id);
      
      if (!video) {
        return res.status(404).json({ message: "Video not found" });
      }

      // If already completed or failed, return cached data
      if (video.status === "completed" && video.videoUrl) {
        return res.json({
          status: video.status,
          videoUrl: video.videoUrl,
          thumbnailUrl: video.thumbnailUrl,
        });
      }

      if (video.status === "failed") {
        return res.json({
          status: video.status,
          videoUrl: video.videoUrl,
          thumbnailUrl: video.thumbnailUrl,
        });
      }

      // Check HeyGen status
      let heygenData = null;
      let successKey = null;

      // Try database keys FIRST
      const activeKeys = await storage.getApiKeys("heygen");
      const filteredKeys = activeKeys.filter(k => k.isActive === "true");
      
      for (const apiKey of filteredKeys) {
        try {
          const response = await fetch(`https://api.heygen.com/v1/video_status.get?video_id=${video.videoId}`, {
            method: "GET",
            headers: { "accept": "application/json", "x-api-key": apiKey.key }
          });
          const data = await response.json() as any;
          if (!data.error) {
            heygenData = data;
            successKey = apiKey;
            break;
          }
        } catch (e) {}
      }

      // If no custom keys worked, try the primary key as a last resort
      if (!heygenData && HEYGEN_API_KEY) {
        try {
          const response = await fetch(`https://api.heygen.com/v1/video_status.get?video_id=${video.videoId}`, {
            method: "GET",
            headers: { "accept": "application/json", "x-api-key": HEYGEN_API_KEY }
          });
          const data = await response.json() as any;
          if (!data.error) {
            heygenData = data;
          }
        } catch (e) {}
      }

      if (!heygenData) {
        return res.status(500).json({ message: "Failed to check status with any API key" });
      }
      
      let status = video.status;
      let videoUrl = video.videoUrl;
      let thumbnailUrl = video.thumbnailUrl;

      if (heygenData.data) {
        status = heygenData.data.status || "pending";
        
        if (status === "completed" && video.status !== "completed") {
          const rawVideoUrl = heygenData.data.video_url;
          thumbnailUrl = heygenData.data.thumbnail_url || null;
          
          try {
            const processedFilename = `processed_${video.id}.mp4`;
            const publicDir = path.join(process.cwd(), "public", "processed_videos");
            const outputPath = path.join(publicDir, processedFilename);
            const tempInputPath = path.join(publicDir, `temp_input_${video.id}.mp4`);
            
            // Check for uploaded banner first, then fall back to original asset
            let overlayPath = path.join(process.cwd(), "public", "banners", "current_banner.png");
            if (!fs.existsSync(overlayPath)) {
              overlayPath = path.join(process.cwd(), "attached_assets", "GET_A_FREE_RATE_REVIEW_1769255824005.png");
            }

            // Ensure directory exists
            if (!fs.existsSync(publicDir)) {
              fs.mkdirSync(publicDir, { recursive: true });
            }

            console.log(`Starting FFmpeg processing for video ${video.id}`);
            console.log(`Input: ${rawVideoUrl}`);
            console.log(`Overlay: ${overlayPath}`);
            console.log(`Output: ${outputPath}`);

            // Step 1: Download the source video first to avoid streaming corruption
            console.log(`Downloading source video to ${tempInputPath}...`);
            const videoResponse = await fetch(rawVideoUrl);
            if (!videoResponse.ok) {
              throw new Error(`Failed to download source video: ${videoResponse.status}`);
            }
            const videoBuffer = await videoResponse.arrayBuffer();
            fs.writeFileSync(tempInputPath, Buffer.from(videoBuffer));
            console.log(`Downloaded source video: ${fs.statSync(tempInputPath).size} bytes`);

            if (!fs.existsSync(overlayPath)) {
              console.warn(`Overlay file not found, skipping overlay for video ${video.id}: ${overlayPath}`);
              // Fallback: just copy the video without overlay if overlay missing
              fs.copyFileSync(tempInputPath, outputPath);
            } else {
              // Step 2: Process the local video file with overlay
              await new Promise((resolve, reject) => {
                ffmpeg(tempInputPath)
                  .input(overlayPath)
                  .complexFilter([
                    "[0:v]format=yuv420p,scale=trunc(iw/2)*2:trunc(ih/2)*2[video]",
                    "[1:v]format=rgba,scale=720:-1[overlay]",
                    "[video][overlay]overlay=0:H-h:format=auto[out]"
                  ])
                  .outputOptions([
                    "-map [out]",
                    "-map 0:a?",
                    "-c:v libx264",
                    "-preset medium",
                    "-crf 23",
                    "-profile:v baseline",
                    "-level 3.0",
                    "-pix_fmt yuv420p",
                    "-c:a aac",
                    "-b:a 128k",
                    "-ar 44100",
                    "-shortest",
                    "-f mp4"
                  ])
                  .on("start", (commandLine) => {
                    console.log("Spawned FFmpeg with command: " + commandLine);
                  })
                  .on("end", () => {
                    console.log(`FFmpeg processing finished for video ${video.id}`);
                    // Clean up temp file
                    try { fs.unlinkSync(tempInputPath); } catch (e) {}
                    resolve(true);
                  })
                  .on("error", (err, stdout, stderr) => {
                    console.error(`FFmpeg error for video ${video.id}:`, err);
                    console.error("FFmpeg stderr:", stderr);
                    // Clean up temp file
                    try { fs.unlinkSync(tempInputPath); } catch (e) {}
                    reject(err);
                  })
                  .save(outputPath);
              });
            }

            videoUrl = `/processed_videos/${processedFilename}`;
            
            await storage.updateVideo(id, {
              status: "completed",
              videoUrl,
              thumbnailUrl,
            });
          } catch (ffmpegError) {
            console.error("FFmpeg processing failed:", ffmpegError);
            // Fallback to original video if processing fails so at least something is playable
            videoUrl = rawVideoUrl;
            if (!videoUrl) {
              console.error("FFmpeg failed and no raw video URL available from HeyGen for video", id);
              throw new Error("Video processing failed and no source URL available");
            }
            await storage.updateVideo(id, {
              status: "completed",
              videoUrl,
              thumbnailUrl,
            });
          }
        } else if (status === "failed") {
          console.error(`HeyGen video status for video ${id} is failed. Response data:`, heygenData);
          await storage.updateVideo(id, { status: "failed" });
        } else if (status === "processing" || status === "pending") {
          // Auto-terminate if HeyGen has been processing/pending for more than 20 minutes
          const TIMEOUT_MS = 20 * 60 * 1000; // 20 minutes
          const createdAt = new Date(video.createdAt).getTime();
          const now = Date.now();
          if ((now - createdAt) > TIMEOUT_MS) {
            console.log(`Video ${id} has been stuck at HeyGen (${status}) for over 20 minutes, auto-terminating and deleting from HeyGen`);
            
            // Try to delete from HeyGen to free up concurrency slot
            const deleteApiKey = successKey?.key || HEYGEN_API_KEY;
            if (video.videoId && deleteApiKey) {
              await deleteVideoFromHeyGen(video.videoId, deleteApiKey);
            }
            
            await storage.updateVideo(id, { status: "failed" });
            status = "failed";
          } else {
            await storage.updateVideo(id, { status: status as "pending" | "processing" });
          }
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

  // Reprocess a single video with current banner
  app.post("/api/videos/:id/reprocess", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const video = await storage.getVideo(id);
      
      if (!video) {
        return res.status(404).json({ message: "Video not found" });
      }
      
      if (!video.videoId) {
        return res.status(400).json({ message: "No HeyGen video ID found for this video" });
      }

      // Get active API key from database
      const keys = await storage.getApiKeys("heygen");
      const activeKey = keys.find(k => k.isActive === "true");
      if (!activeKey) {
        return res.status(400).json({ message: "No active HeyGen API key found" });
      }

      // Get the original video URL from HeyGen
      const statusResponse = await fetch(
        `https://api.heygen.com/v1/video_status.get?video_id=${video.videoId}`,
        {
          method: "GET",
          headers: {
            "accept": "application/json",
            "x-api-key": activeKey.key,
          },
        }
      );
      const statusData = await statusResponse.json() as any;
      const rawVideoUrl = statusData.data?.video_url;

      if (!rawVideoUrl) {
        return res.status(400).json({ message: "Could not retrieve original video URL from HeyGen" });
      }

      // Check for uploaded banner first, then fall back to original asset
      let overlayPath = path.join(process.cwd(), "public", "banners", "current_banner.png");
      if (!fs.existsSync(overlayPath)) {
        overlayPath = path.join(process.cwd(), "attached_assets", "GET_A_FREE_RATE_REVIEW_1769255824005.png");
      }

      const processedFilename = `processed_${video.id}.mp4`;
      const publicDir = path.join(process.cwd(), "public", "processed_videos");
      const outputPath = path.join(publicDir, processedFilename);

      // Ensure directory exists
      if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir, { recursive: true });
      }

      // Download HeyGen video to temp file first to avoid streaming issues
      const tempInputPath = path.join(publicDir, `temp_input_${video.id}.mp4`);
      const videoResponse = await fetch(rawVideoUrl);
      const videoBuffer = await videoResponse.arrayBuffer();
      fs.writeFileSync(tempInputPath, Buffer.from(videoBuffer));

      await new Promise((resolve, reject) => {
        ffmpeg(tempInputPath)
          .input(overlayPath)
          .complexFilter([
            "[0:v]format=yuv420p,scale=trunc(iw/2)*2:trunc(ih/2)*2[video]",
            "[1:v]format=rgba,scale=720:-1[overlay]",
            "[video][overlay]overlay=0:H-h:format=auto[out]"
          ])
          .outputOptions([
            "-map [out]",
            "-map 0:a?",
            "-c:v libx264",
            "-preset medium",
            "-crf 23",
            "-profile:v baseline",
            "-level 3.0",
            "-pix_fmt yuv420p",
            "-c:a aac",
            "-b:a 128k",
            "-ar 44100",
            "-shortest",
            "-f mp4"
          ])
          .on("start", (commandLine) => {
            console.log("Reprocess FFmpeg command: " + commandLine);
          })
          .on("end", () => {
            console.log(`Reprocessing finished for video ${video.id}`);
            try { fs.unlinkSync(tempInputPath); } catch (e) {}
            resolve(true);
          })
          .on("error", (err) => {
            console.error(`Reprocess FFmpeg error for video ${video.id}:`, err);
            try { fs.unlinkSync(tempInputPath); } catch (e) {}
            reject(err);
          })
          .save(outputPath);
      });

      const newUrl = `/processed_videos/${processedFilename}`;
      await storage.updateVideo(video.id, { videoUrl: newUrl });

      res.json({ message: "Video reprocessed successfully", videoUrl: newUrl });
    } catch (error) {
      console.error("Error reprocessing video:", error);
      res.status(500).json({ message: "Failed to reprocess video" });
    }
  });

  // Delete a video (both from database and HeyGen)
  app.delete("/api/videos/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const video = await storage.getVideo(id);
      
      if (!video) {
        return res.status(404).json({ message: "Video not found" });
      }

      // Try to delete from HeyGen first
      if (video.videoId) {
        const keys = await storage.getApiKeys("heygen");
        const activeKey = keys.find(k => k.isActive === "true");
        const apiKey = activeKey?.key || HEYGEN_API_KEY;
        
        if (apiKey) {
          await deleteVideoFromHeyGen(video.videoId, apiKey);
        }
      }

      // Delete from local storage and database
      await storage.deleteVideo(id);
      
      res.json({ message: "Video deleted successfully" });
    } catch (error) {
      console.error("Error deleting video:", error);
      res.status(500).json({ message: "Failed to delete video" });
    }
  });

  return httpServer;
}
