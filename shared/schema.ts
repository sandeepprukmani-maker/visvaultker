import { sqliteTable, text, integer, blob } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// === AUTOMATION TABLES ===
export const automations = sqliteTable("automations", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  prompt: text("prompt").notNull(),
  status: text("status").notNull().default("pending"), // pending, running, completed, failed
  result: text("result", { mode: 'json' }), // For extracted data or success message
  screenshot: text("screenshot"), // Base64 or URL
  error: text("error"),
  createdAt: integer("created_at", { mode: 'timestamp' }).defaultNow(),
});

export const automationLogs = sqliteTable("automation_logs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  automationId: integer("automation_id").notNull(),
  message: text("message").notNull(),
  type: text("type").notNull().default("info"), // info, error, action
  timestamp: integer("timestamp", { mode: 'timestamp' }).defaultNow(),
});

// === RELATIONS ===
export const automationsRelations = relations(automations, ({ many }) => ({
  logs: many(automationLogs),
}));

export const automationLogsRelations = relations(automationLogs, ({ one }) => ({
  automation: one(automations, {
    fields: [automationLogs.automationId],
    references: [automations.id],
  }),
}));

// === SCHEMAS ===
export const insertAutomationSchema = createInsertSchema(automations).pick({
  prompt: true,
});

export const insertAutomationLogSchema = createInsertSchema(automationLogs).pick({
  automationId: true,
  message: true,
  type: true,
});

// === TYPES ===
export type Automation = typeof automations.$inferSelect;
export type InsertAutomation = z.infer<typeof insertAutomationSchema>;
export type AutomationLog = typeof automationLogs.$inferSelect;
export type InsertAutomationLog = z.infer<typeof insertAutomationLogSchema>;

// API Types
export type CreateAutomationRequest = InsertAutomation;
export type AutomationResponse = Automation & { logs?: AutomationLog[] };
