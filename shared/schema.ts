import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, jsonb, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Automation execution record
export const automations = pgTable("automations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  prompt: text("prompt").notNull(),
  status: text("status").notNull(), // 'pending' | 'running' | 'success' | 'error'
  model: text("model").notNull(), // 'openai' | 'anthropic' | 'gemini'
  result: jsonb("result"), // Execution result with extracted data
  logs: jsonb("logs"), // Array of action logs
  error: text("error"),
  duration: text("duration"), // Execution duration in ms
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Cached automation patterns
export const cache = pgTable("cache", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  prompt: text("prompt").notNull(),
  pattern: jsonb("pattern").notNull(), // Cached action pattern
  useCount: text("use_count").default("0"), // Number of times used
  lastUsed: timestamp("last_used").defaultNow(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// User settings
export const settings = pgTable("settings", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  selectedModel: text("selected_model").notNull().default("openai"),
  screenshotMode: text("screenshot_mode").notNull().default("none"), // 'every_step' | 'last_step' | 'none'
  theme: text("theme").notNull().default("light"), // 'light' | 'dark'
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// Zod schemas for validation
export const insertAutomationSchema = createInsertSchema(automations).omit({
  id: true,
  createdAt: true,
});

export const insertCacheSchema = createInsertSchema(cache).omit({
  id: true,
  createdAt: true,
  lastUsed: true,
});

export const insertSettingsSchema = createInsertSchema(settings).omit({
  id: true,
  updatedAt: true,
});

// TypeScript types
export type Automation = typeof automations.$inferSelect;
export type InsertAutomation = z.infer<typeof insertAutomationSchema>;

export type Cache = typeof cache.$inferSelect;
export type InsertCache = z.infer<typeof insertCacheSchema>;

export type Settings = typeof settings.$inferSelect;
export type InsertSettings = z.infer<typeof insertSettingsSchema>;

// WebSocket message types
export const wsMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("execution_started"),
    data: z.object({
      automationId: z.string(),
      prompt: z.string(),
    }),
  }),
  z.object({
    type: z.literal("execution_log"),
    data: z.object({
      automationId: z.string(),
      log: z.object({
        timestamp: z.number(),
        action: z.string(),
        status: z.string(),
        details: z.any().optional(),
      }),
    }),
  }),
  z.object({
    type: z.literal("execution_completed"),
    data: z.object({
      automationId: z.string(),
      result: z.any(),
      duration: z.string(),
    }),
  }),
  z.object({
    type: z.literal("execution_error"),
    data: z.object({
      automationId: z.string(),
      error: z.string(),
    }),
  }),
]);

export type WSMessage = z.infer<typeof wsMessageSchema>;
