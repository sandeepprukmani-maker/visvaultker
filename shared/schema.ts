import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, jsonb, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Workflow step schema
export const workflowStepSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  status: z.enum(["pending", "running", "completed", "failed", "paused"]),
  tool: z.string().optional(),
  dependencies: z.array(z.string()).optional(),
  result: z.string().optional(),
  error: z.string().optional(),
});

export type WorkflowStep = z.infer<typeof workflowStepSchema>;

// Workflow schema
export const workflowSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  steps: z.array(workflowStepSchema),
});

export type Workflow = z.infer<typeof workflowSchema>;

// Execution status enum
export const executionStatusEnum = z.enum([
  "planning",
  "ready",
  "running",
  "paused",
  "completed",
  "failed",
  "cancelled"
]);

export type ExecutionStatus = z.infer<typeof executionStatusEnum>;

// Execution log entry
export const logEntrySchema = z.object({
  timestamp: z.string(),
  level: z.enum(["info", "warning", "error", "success"]),
  message: z.string(),
  stepId: z.string().optional(),
});

export type LogEntry = z.infer<typeof logEntrySchema>;

// Execution record for history
export const executions = pgTable("executions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  prompt: text("prompt").notNull(),
  status: text("status").notNull().default("planning"),
  workflow: jsonb("workflow"),
  logs: jsonb("logs").default([]),
  result: text("result"),
  error: text("error"),
  progress: integer("progress").default(0),
  currentStep: text("current_step"),
  createdAt: timestamp("created_at").defaultNow(),
  completedAt: timestamp("completed_at"),
});

export const insertExecutionSchema = createInsertSchema(executions).omit({
  id: true,
  createdAt: true,
  completedAt: true,
});

export type InsertExecution = z.infer<typeof insertExecutionSchema>;
export type Execution = typeof executions.$inferSelect;

// Template schema
export const templateSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  prompt: z.string(),
  icon: z.string(),
  category: z.enum(["scraping", "forms", "extraction", "research", "custom"]),
});

export type Template = z.infer<typeof templateSchema>;

// Model options
export const modelOptions = ["anthropic", "openai"] as const;
export const modelOptionSchema = z.enum(modelOptions);
export type ModelOption = z.infer<typeof modelOptionSchema>;

// API request/response types
export const generateWorkflowRequest = z.object({
  prompt: z.string().min(1, "Please enter a task description"),
  model: modelOptionSchema.default("anthropic"),
});

export type GenerateWorkflowRequest = z.infer<typeof generateWorkflowRequest>;

export const executeWorkflowRequest = z.object({
  executionId: z.string(),
});

export type ExecuteWorkflowRequest = z.infer<typeof executeWorkflowRequest>;

export const controlWorkflowRequest = z.object({
  executionId: z.string(),
  action: z.enum(["pause", "resume", "cancel"]),
});

export type ControlWorkflowRequest = z.infer<typeof controlWorkflowRequest>;

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
