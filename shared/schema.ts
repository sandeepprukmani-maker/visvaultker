import { z } from "zod";

export const actionStatusSchema = z.enum(["pending", "running", "success", "error"]);
export type ActionStatus = z.infer<typeof actionStatusSchema>;

export const browserActionSchema = z.object({
  id: z.string(),
  type: z.string(),
  target: z.string().optional(),
  value: z.string().optional(),
  status: actionStatusSchema,
  timestamp: z.number(),
  result: z.string().optional(),
  error: z.string().optional(),
});
export type BrowserAction = z.infer<typeof browserActionSchema>;

export const automationTaskSchema = z.object({
  id: z.string(),
  prompt: z.string(),
  status: actionStatusSchema,
  actions: z.array(browserActionSchema),
  result: z.string().optional(),
  error: z.string().optional(),
  createdAt: z.number(),
  completedAt: z.number().optional(),
});
export type AutomationTask = z.infer<typeof automationTaskSchema>;

export const insertTaskSchema = z.object({
  prompt: z.string().min(1, "Prompt is required"),
});
export type InsertTask = z.infer<typeof insertTaskSchema>;

export const messageSchema = z.object({
  id: z.string(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  timestamp: z.number(),
  taskId: z.string().optional(),
  actions: z.array(browserActionSchema).optional(),
});
export type Message = z.infer<typeof messageSchema>;

export const connectionStatusSchema = z.enum(["connected", "disconnected", "connecting"]);
export type ConnectionStatus = z.infer<typeof connectionStatusSchema>;
