import { z } from "zod";
import { pgTable, text, timestamp, jsonb, vector, serial, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { sql } from "drizzle-orm";

// Automation request schema
export const automationModeSchema = z.enum(["act", "observe", "extract", "agent"]);
export type AutomationMode = z.infer<typeof automationModeSchema>;

// Unified automation request - system auto-detects URL and appropriate mode
export const unifiedAutomationRequestSchema = z.object({
  prompt: z.string().min(1), // Natural language prompt including URL and task
  model: z.string().default("google/gemini-2.5-flash"),
});
export type UnifiedAutomationRequest = z.infer<typeof unifiedAutomationRequestSchema>;

// Legacy automation request (for backward compatibility)
export const automationRequestSchema = z.object({
  url: z.string().url(),
  prompt: z.string().min(1),
  mode: automationModeSchema,
  model: z.string().default("google/gemini-2.5-flash"),
});
export type AutomationRequest = z.infer<typeof automationRequestSchema>;

// Log entry schema
export const logEntryStatusSchema = z.enum(["success", "error", "pending", "running"]);
export type LogEntryStatus = z.infer<typeof logEntryStatusSchema>;

export const logEntrySchema = z.object({
  id: z.string(),
  timestamp: z.number(),
  action: z.string(),
  status: logEntryStatusSchema,
  selector: z.string().optional(),
  description: z.string().optional(),
});
export type LogEntry = z.infer<typeof logEntrySchema>;

// Automation response schema
export const automationResponseSchema = z.object({
  success: z.boolean(),
  sessionId: z.string(),
  logs: z.array(logEntrySchema),
  generatedCode: z.object({
    typescript: z.string().optional(), // LLM-based code (act/observe/extract)
    cached: z.string().optional(), // Code with caching enabled
    agent: z.string().optional(), // Agent-based code
    locators: z.string().optional(), // Rerunnable code with locators/deepLocators
  }),
  error: z.string().optional(),
  detectedUrl: z.string().optional(), // Auto-detected URL from prompt
  usedModes: z.array(automationModeSchema).optional(), // Which modes were used
  screenshot: z.string().optional(), // Base64 encoded screenshot
});
export type AutomationResponse = z.infer<typeof automationResponseSchema>;

// WebSocket message types
export const wsLogMessageSchema = z.object({
  type: z.literal("log"),
  sessionId: z.string(),
  log: logEntrySchema,
});

export const wsCompleteMessageSchema = z.object({
  type: z.literal("complete"),
  sessionId: z.string(),
  response: automationResponseSchema,
});

export const wsErrorMessageSchema = z.object({
  type: z.literal("error"),
  sessionId: z.string(),
  error: z.string(),
});

export const wsMessageSchema = z.union([
  wsLogMessageSchema,
  wsCompleteMessageSchema,
  wsErrorMessageSchema,
]);

export type WSMessage = z.infer<typeof wsMessageSchema>;

// Database schema for automation history with semantic caching
export const automationHistory = pgTable("automation_history", {
  id: serial("id").primaryKey(),
  prompt: text("prompt").notNull(),
  promptEmbedding: vector("prompt_embedding", { dimensions: 1536 }), // OpenAI text-embedding-3-small uses 1536 dimensions
  detectedUrl: text("detected_url"),
  mode: text("mode").notNull(),
  model: text("model").notNull(),
  success: boolean("success").notNull(),
  sessionId: text("session_id").notNull(),
  logs: jsonb("logs").$type<LogEntry[]>().notNull(),
  generatedCode: jsonb("generated_code").$type<{
    typescript?: string;
    cached?: string;
    agent?: string;
    locators?: string;
  }>().notNull(),
  screenshot: text("screenshot"), // Base64 encoded screenshot
  error: text("error"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertAutomationHistorySchema = createInsertSchema(automationHistory).omit({
  id: true,
  createdAt: true,
  promptEmbedding: true,
});

export type InsertAutomationHistory = z.infer<typeof insertAutomationHistorySchema>;
export type AutomationHistory = typeof automationHistory.$inferSelect;
export type AutomationHistoryInsert = typeof automationHistory.$inferInsert;
