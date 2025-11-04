import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, integer, jsonb, boolean, real } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const tasks = pgTable("tasks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  description: text("description"),
  category: text("category"),
  tags: text("tags").array(),
  websiteUrl: text("website_url").notNull(),
  steps: jsonb("steps").notNull(),
  parameters: jsonb("parameters"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
  userId: varchar("user_id").references(() => users.id),
});

export const workflows = pgTable("workflows", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  description: text("description"),
  tags: text("tags").array(),
  enabled: boolean("enabled").default(true).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
  userId: varchar("user_id").references(() => users.id),
});

export const workflowTasks = pgTable("workflow_tasks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  workflowId: varchar("workflow_id").references(() => workflows.id).notNull(),
  taskId: varchar("task_id").references(() => tasks.id).notNull(),
  order: integer("order").notNull(),
  condition: text("condition"),
  parameters: jsonb("parameters"),
});

export const websiteProfiles = pgTable("website_profiles", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  url: text("url").notNull().unique(),
  name: text("name").notNull(),
  domStructure: jsonb("dom_structure").notNull(),
  interactionGraph: jsonb("interaction_graph"),
  elementMap: jsonb("element_map"),
  screenshots: text("screenshots").array(),
  lastExplored: timestamp("last_explored").defaultNow().notNull(),
  version: integer("version").default(1).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const executions = pgTable("executions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  taskId: varchar("task_id").references(() => tasks.id),
  workflowId: varchar("workflow_id").references(() => workflows.id),
  status: text("status").notNull(),
  startedAt: timestamp("started_at").defaultNow().notNull(),
  completedAt: timestamp("completed_at"),
  result: jsonb("result"),
  error: text("error"),
  logs: jsonb("logs"),
  screenshots: text("screenshots").array(),
  userId: varchar("user_id").references(() => users.id),
});

export const llmUsage = pgTable("llm_usage", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  provider: text("provider").notNull(),
  model: text("model").notNull(),
  taskType: text("task_type").notNull(),
  promptTokens: integer("prompt_tokens").notNull(),
  completionTokens: integer("completion_tokens").notNull(),
  totalCost: real("total_cost").notNull(),
  executionId: varchar("execution_id").references(() => executions.id),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

export const insertUserSchema = createInsertSchema(users).omit({ id: true });
export const insertTaskSchema = createInsertSchema(tasks).omit({ id: true, createdAt: true, updatedAt: true });
export const insertWorkflowSchema = createInsertSchema(workflows).omit({ id: true, createdAt: true, updatedAt: true });
export const insertWorkflowTaskSchema = createInsertSchema(workflowTasks).omit({ id: true });
export const insertWebsiteProfileSchema = createInsertSchema(websiteProfiles).omit({ id: true, createdAt: true, lastExplored: true });
export const insertExecutionSchema = createInsertSchema(executions).omit({ id: true, startedAt: true });
export const insertLlmUsageSchema = createInsertSchema(llmUsage).omit({ id: true, timestamp: true });

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Task = typeof tasks.$inferSelect;
export type InsertTask = z.infer<typeof insertTaskSchema>;
export type Workflow = typeof workflows.$inferSelect;
export type InsertWorkflow = z.infer<typeof insertWorkflowSchema>;
export type WorkflowTask = typeof workflowTasks.$inferSelect;
export type InsertWorkflowTask = z.infer<typeof insertWorkflowTaskSchema>;
export type WebsiteProfile = typeof websiteProfiles.$inferSelect;
export type InsertWebsiteProfile = z.infer<typeof insertWebsiteProfileSchema>;
export type Execution = typeof executions.$inferSelect;
export type InsertExecution = z.infer<typeof insertExecutionSchema>;
export type LlmUsage = typeof llmUsage.$inferSelect;
export type InsertLlmUsage = z.infer<typeof insertLlmUsageSchema>;
