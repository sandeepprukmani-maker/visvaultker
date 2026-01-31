import { db } from "./db";
import { videos, apiKeys, type Video, type InsertVideo, type ApiKey, type InsertApiKey } from "@shared/schema";
import { eq, desc, and, asc } from "drizzle-orm";
import path from "path";
import fs from "fs";

export interface IStorage {
  getVideos(): Promise<Video[]>;
  getVideo(id: number): Promise<Video | undefined>;
  getVideoByVideoId(videoId: string): Promise<Video | undefined>;
  createVideo(video: InsertVideo): Promise<Video>;
  updateVideo(id: number, updates: Partial<InsertVideo>): Promise<Video>;
  deleteVideo(id: number): Promise<void>;
  
  // API Key management
  getApiKeys(service: string): Promise<ApiKey[]>;
  createApiKey(apiKey: InsertApiKey): Promise<ApiKey>;
  updateApiKey(id: number, updates: Partial<ApiKey>): Promise<ApiKey>;
  deleteApiKey(id: number): Promise<void>;
  getNextApiKey(service: string): Promise<ApiKey | undefined>;
}

export class DatabaseStorage implements IStorage {
  async getVideos(): Promise<Video[]> {
    return await db.select().from(videos).orderBy(desc(videos.createdAt));
  }

  async getVideo(id: number): Promise<Video | undefined> {
    const [video] = await db.select().from(videos).where(eq(videos.id, id));
    return video;
  }

  async getVideoByVideoId(videoId: string): Promise<Video | undefined> {
    const [video] = await db.select().from(videos).where(eq(videos.videoId, videoId));
    return video;
  }

  async createVideo(video: InsertVideo): Promise<Video> {
    const [created] = await db.insert(videos).values(video).returning();
    
    // Maintain max 5 videos
    const allVideos = await db.select().from(videos).orderBy(desc(videos.createdAt));
    if (allVideos.length > 5) {
      const videosToDelete = allVideos.slice(5);
      for (const v of videosToDelete) {
        // Delete processed file if it exists
        if (v.videoUrl && v.videoUrl.startsWith("/processed_videos/")) {
          const filePath = path.join(process.cwd(), "public", v.videoUrl);
          if (fs.existsSync(filePath)) {
            try {
              fs.unlinkSync(filePath);
            } catch (err) {
              console.error(`Failed to delete video file ${filePath}:`, err);
            }
          }
        }
        await db.delete(videos).where(eq(videos.id, v.id));
      }
    }
    
    return created;
  }

  async updateVideo(id: number, updates: Partial<InsertVideo>): Promise<Video> {
    const [updated] = await db
      .update(videos)
      .set(updates)
      .where(eq(videos.id, id))
      .returning();
    return updated;
  }

  async deleteVideo(id: number): Promise<void> {
    const video = await this.getVideo(id);
    if (video) {
      if (video.videoUrl && video.videoUrl.startsWith("/processed_videos/")) {
        const filePath = path.join(process.cwd(), "public", video.videoUrl);
        if (fs.existsSync(filePath)) {
          try {
            fs.unlinkSync(filePath);
          } catch (err) {
            console.error(`Failed to delete video file ${filePath}:`, err);
          }
        }
      }
      await db.delete(videos).where(eq(videos.id, id));
    }
  }

  async getApiKeys(service: string): Promise<ApiKey[]> {
    return await db.select().from(apiKeys).where(eq(apiKeys.service, service)).orderBy(desc(apiKeys.createdAt));
  }

  async createApiKey(apiKey: InsertApiKey): Promise<ApiKey> {
    const [created] = await db.insert(apiKeys).values({
      key: apiKey.key,
      service: apiKey.service,
      isActive: apiKey.isActive ?? "true",
    }).returning();
    return created;
  }

  async updateApiKey(id: number, updates: Partial<ApiKey>): Promise<ApiKey> {
    const [updated] = await db
      .update(apiKeys)
      .set(updates)
      .where(eq(apiKeys.id, id))
      .returning();
    return updated;
  }

  async deleteApiKey(id: number): Promise<void> {
    await db.delete(apiKeys).where(eq(apiKeys.id, id));
  }

  async getNextApiKey(service: string): Promise<ApiKey | undefined> {
    // Basic rotation: get the active key used longest ago with low failure count
    const [key] = await db
      .select()
      .from(apiKeys)
      .where(and(eq(apiKeys.service, service), eq(apiKeys.isActive, "true")))
      .orderBy(asc(apiKeys.lastUsedAt))
      .limit(1);
    
    if (key) {
      await this.updateApiKey(key.id, { lastUsedAt: new Date() });
    }
    return key;
  }
}

export const storage = new DatabaseStorage();
