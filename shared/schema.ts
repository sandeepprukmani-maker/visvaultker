import { z } from "zod";

// Automation request schema
export const automationModeSchema = z.enum(["act", "observe", "extract", "agent"]);
export type AutomationMode = z.infer<typeof automationModeSchema>;

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
    typescript: z.string().optional(),
    cached: z.string().optional(),
    agent: z.string().optional(),
  }),
  error: z.string().optional(),
});
export type AutomationResponse = z.infer<typeof automationResponseSchema>;
