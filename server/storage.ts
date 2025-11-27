import { type User, type InsertUser, type AutomationJob, type InsertAutomationJob, users, automationJobs } from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  createJob(job: InsertAutomationJob): Promise<AutomationJob>;
  getJob(id: number): Promise<AutomationJob | undefined>;
  updateJob(id: number, updates: Partial<AutomationJob>): Promise<AutomationJob | undefined>;
  listJobs(limit?: number): Promise<AutomationJob[]>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const result = await db.select().from(users).where(eq(users.id, id));
    return result[0];
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const result = await db.select().from(users).where(eq(users.username, username));
    return result[0];
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const result = await db.insert(users).values(insertUser).returning();
    return result[0];
  }

  async createJob(insertJob: InsertAutomationJob): Promise<AutomationJob> {
    const result = await db.insert(automationJobs).values({
      prompt: insertJob.prompt,
      status: insertJob.status || "pending",
      steps: insertJob.steps || [],
      result: insertJob.result || null,
      error: insertJob.error || null,
    }).returning();
    return result[0];
  }

  async getJob(id: number): Promise<AutomationJob | undefined> {
    const result = await db.select().from(automationJobs).where(eq(automationJobs.id, id));
    return result[0];
  }

  async updateJob(id: number, updates: Partial<AutomationJob>): Promise<AutomationJob | undefined> {
    const result = await db.update(automationJobs)
      .set(updates)
      .where(eq(automationJobs.id, id))
      .returning();
    return result[0];
  }

  async listJobs(limit = 50): Promise<AutomationJob[]> {
    return db.select()
      .from(automationJobs)
      .orderBy(desc(automationJobs.createdAt))
      .limit(limit);
  }
}

export const storage = new DatabaseStorage();
