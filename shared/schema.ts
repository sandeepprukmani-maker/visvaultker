import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, timestamp, jsonb, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const crawlSessions = pgTable("crawl_sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  url: text("url").notNull(),
  depth: integer("depth").notNull().default(3),
  status: text("status").notNull().default("pending"),
  pagesFound: integer("pages_found").notNull().default(0),
  elementsFound: integer("elements_found").notNull().default(0),
  startedAt: timestamp("started_at").notNull().defaultNow(),
  completedAt: timestamp("completed_at"),
});

export const pages = pgTable("pages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  crawlSessionId: varchar("crawl_session_id").notNull().references(() => crawlSessions.id),
  url: text("url").notNull(),
  title: text("title").notNull(),
  elementCount: integer("element_count").notNull().default(0),
  screenshot: text("screenshot"),
  templateHash: text("template_hash"),
  templateGroup: integer("template_group"),
  crawledAt: timestamp("crawled_at").notNull().defaultNow(),
});

export const elements = pgTable("elements", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  pageId: varchar("page_id").notNull().references(() => pages.id),
  tag: text("tag").notNull(),
  selector: text("selector").notNull(),
  text: text("text"),
  attributes: jsonb("attributes").notNull().default({}),
  xpath: text("xpath"),
  confidence: integer("confidence").notNull().default(100),
  embedding: text("embedding"),
});

export const automations = pgTable("automations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  command: text("command").notNull(),
  status: text("status").notNull().default("queued"),
  plan: jsonb("plan"),
  result: jsonb("result"),
  duration: integer("duration"),
  actionCount: integer("action_count").notNull().default(0),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  completedAt: timestamp("completed_at"),
});

export const automationLogs = pgTable("automation_logs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  automationId: varchar("automation_id").notNull().references(() => automations.id),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  action: text("action").notNull(),
  status: text("status").notNull(),
  details: text("details"),
  screenshot: text("screenshot"),
});

// Insert schemas
export const insertCrawlSessionSchema = createInsertSchema(crawlSessions).omit({
  id: true,
  pagesFound: true,
  elementsFound: true,
  startedAt: true,
  completedAt: true,
});

export const insertPageSchema = createInsertSchema(pages).omit({
  id: true,
  crawledAt: true,
});

export const insertElementSchema = createInsertSchema(elements).omit({
  id: true,
});

export const insertAutomationSchema = createInsertSchema(automations).omit({
  id: true,
  status: true,
  createdAt: true,
  completedAt: true,
  duration: true,
  actionCount: true,
});

export const insertAutomationLogSchema = createInsertSchema(automationLogs).omit({
  id: true,
  timestamp: true,
});

// Types
export type InsertCrawlSession = z.infer<typeof insertCrawlSessionSchema>;
export type CrawlSession = typeof crawlSessions.$inferSelect;

export type InsertPage = z.infer<typeof insertPageSchema>;
export type Page = typeof pages.$inferSelect;

export type InsertElement = z.infer<typeof insertElementSchema>;
export type Element = typeof elements.$inferSelect;

export type InsertAutomation = z.infer<typeof insertAutomationSchema>;
export type Automation = typeof automations.$inferSelect;

export type InsertAutomationLog = z.infer<typeof insertAutomationLogSchema>;
export type AutomationLog = typeof automationLogs.$inferSelect;
