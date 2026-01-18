import { pgTable, text, serial, timestamp, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// === TABLE DEFINITIONS ===

export const posts = pgTable("posts", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  link: text("link").notNull(),
  content: text("content"),
  pubDate: text("pub_date"), // Keeping as text for simplicity from RSS
  guid: text("guid").unique().notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const posters = pgTable("posters", {
  id: serial("id").primaryKey(),
  postId: integer("post_id").references(() => posts.id).notNull(),
  caption: text("caption").notNull(),
  htmlContent: text("html_content"), // Store the generated HTML flyer
  createdAt: timestamp("created_at").defaultNow(),
});

export const videos = pgTable("videos", {
  id: serial("id").primaryKey(),
  postId: integer("post_id").references(() => posts.id).notNull(),
  videoId: text("video_id").notNull(), // HeyGen video ID
  status: text("status").notNull().default("processing"), // processing, completed, failed
  videoUrl: text("video_url"),
  thumbnailUrl: text("thumbnail_url"),
  script: text("script"),
  createdAt: timestamp("created_at").defaultNow(),
});

// === SCHEMAS ===

export const insertPostSchema = createInsertSchema(posts).omit({ id: true, createdAt: true });
export const insertPosterSchema = createInsertSchema(posters).omit({ id: true, createdAt: true });
export const insertVideoSchema = createInsertSchema(videos).omit({ id: true, createdAt: true });

// === TYPES ===

export type Post = typeof posts.$inferSelect;
export type InsertPost = z.infer<typeof insertPostSchema>;

export type Poster = typeof posters.$inferSelect;
export type InsertPoster = z.infer<typeof insertPosterSchema>;

export type Video = typeof videos.$inferSelect;
export type InsertVideo = z.infer<typeof insertVideoSchema>;

// Request types
export type GeneratePosterRequest = {
  postId: number;
};

export * from "./models/chat";
