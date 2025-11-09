import { z } from "zod";

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
    typescript: z.string().optional(),
    cached: z.string().optional(),
    agent: z.string().optional(),
  }),
  error: z.string().optional(),
  detectedUrl: z.string().optional(), // Auto-detected URL from prompt
  usedModes: z.array(automationModeSchema).optional(), // Which modes were used
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
