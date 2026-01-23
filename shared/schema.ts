import { pgTable, text, serial, timestamp, varchar } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { sql } from "drizzle-orm";

// Users table (kept for compatibility)
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Videos table for storing generated HeyGen videos
export const videos = pgTable("videos", {
  id: serial("id").primaryKey(),
  videoId: text("video_id").notNull(),
  status: text("status").notNull().default("pending"),
  videoUrl: text("video_url"),
  thumbnailUrl: text("thumbnail_url"),
  originalTitle: text("original_title").notNull(),
  originalDescription: text("original_description").notNull(),
  marketingScript: text("marketing_script").notNull(),
  createdAt: timestamp("created_at").default(sql`CURRENT_TIMESTAMP`).notNull(),
});

export const insertVideoSchema = createInsertSchema(videos).omit({
  id: true,
  createdAt: true,
});

export type Video = typeof videos.$inferSelect;
export type InsertVideo = z.infer<typeof insertVideoSchema>;

// RSS Feed item type
export interface RSSItem {
  title: string;
  description: string;
  link: string;
  pubDate: string;
}

// API response types
export type VideoResponse = Video;
export type CreateVideoRequest = {
  originalTitle: string;
  originalDescription: string;
  marketingScript: string;
};
export type VideoStatusResponse = {
  status: string;
  videoUrl?: string;
  thumbnailUrl?: string;
};
