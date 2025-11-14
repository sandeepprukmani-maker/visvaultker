import { pgTable, text, varchar, timestamp, integer, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Automation execution history
export const automationHistory = pgTable("automation_history", {
  id: varchar("id").primaryKey(),
  prompt: text("prompt").notNull(),
  executedCode: text("executed_code"),
  pageState: text("page_state"),
  result: text("result"),
  status: varchar("status", { length: 50 }).notNull(), // 'success', 'error', 'running'
  tokensUsed: integer("tokens_used").default(0),
  executionTime: integer("execution_time").default(0), // milliseconds
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertAutomationHistorySchema = createInsertSchema(automationHistory).omit({
  id: true,
  createdAt: true,
});

export type InsertAutomationHistory = z.infer<typeof insertAutomationHistorySchema>;
export type AutomationHistory = typeof automationHistory.$inferSelect;

// Pre-built automation templates
export const automationTemplate = pgTable("automation_template", {
  id: varchar("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description").notNull(),
  prompt: text("prompt").notNull(),
  category: varchar("category", { length: 50 }).notNull(), // 'navigation', 'form', 'extraction', 'testing'
  icon: varchar("icon", { length: 50 }).notNull(),
});

export const insertAutomationTemplateSchema = createInsertSchema(automationTemplate).omit({
  id: true,
});

export type InsertAutomationTemplate = z.infer<typeof insertAutomationTemplateSchema>;
export type AutomationTemplate = typeof automationTemplate.$inferSelect;

// WebSocket message types for real-time communication
export const WebSocketMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("automation_start"),
    data: z.object({
      prompt: z.string(),
      executionId: z.string(),
    }),
  }),
  z.object({
    type: z.literal("automation_progress"),
    data: z.object({
      executionId: z.string(),
      step: z.string(),
      pageState: z.string().optional(),
    }),
  }),
  z.object({
    type: z.literal("automation_complete"),
    data: z.object({
      executionId: z.string(),
      result: z.string(),
      executedCode: z.string(),
      pageState: z.string(),
      tokensUsed: z.number(),
      executionTime: z.number(),
    }),
  }),
  z.object({
    type: z.literal("automation_error"),
    data: z.object({
      executionId: z.string(),
      error: z.string(),
    }),
  }),
]);

export type WebSocketMessage = z.infer<typeof WebSocketMessageSchema>;

// API request/response types
export const ExecuteAutomationRequestSchema = z.object({
  prompt: z.string().min(1, "Prompt cannot be empty"),
  useTemplate: z.boolean().optional(),
});

export type ExecuteAutomationRequest = z.infer<typeof ExecuteAutomationRequestSchema>;

export const ExecuteAutomationResponseSchema = z.object({
  executionId: z.string(),
  status: z.string(),
});

export type ExecuteAutomationResponse = z.infer<typeof ExecuteAutomationResponseSchema>;

// Token metrics
export const TokenMetricsSchema = z.object({
  totalTokensUsed: z.number(),
  totalExecutions: z.number(),
  averageTokensPerExecution: z.number(),
  estimatedSavings: z.number(), // percentage
  averageExecutionTime: z.number(), // milliseconds
});

export type TokenMetrics = z.infer<typeof TokenMetricsSchema>;
