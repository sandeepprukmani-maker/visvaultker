import { db } from "./db";
import {
  automations,
  automationLogs,
  type InsertAutomation,
  type Automation,
  type InsertAutomationLog,
  type AutomationLog,
} from "@shared/schema";
import { eq, desc } from "drizzle-orm";
export interface IStorage {
  // Automations
  createAutomation(automation: InsertAutomation): Promise<Automation>;
  getAutomation(id: number): Promise<Automation | undefined>;
  listAutomations(): Promise<Automation[]>;
  updateAutomation(id: number, updates: Partial<Automation>): Promise<Automation>;
  
  // Logs
  addLog(log: InsertAutomationLog): Promise<AutomationLog>;
  getLogs(automationId: number): Promise<AutomationLog[]>;
}

export class DatabaseStorage implements IStorage {
  // Automation Methods
  async createAutomation(insertAutomation: InsertAutomation): Promise<Automation> {
    const [automation] = await db
      .insert(automations)
      .values(insertAutomation)
      .returning();
    return automation;
  }

  async getAutomation(id: number): Promise<Automation | undefined> {
    const [automation] = await db
      .select()
      .from(automations)
      .where(eq(automations.id, id));
    return automation;
  }

  async listAutomations(): Promise<Automation[]> {
    return db
      .select()
      .from(automations)
      .orderBy(desc(automations.createdAt));
  }

  async updateAutomation(id: number, updates: Partial<Automation>): Promise<Automation> {
    const [updated] = await db
      .update(automations)
      .set(updates)
      .where(eq(automations.id, id))
      .returning();
    return updated;
  }

  async addLog(insertLog: InsertAutomationLog): Promise<AutomationLog> {
    const [log] = await db
      .insert(automationLogs)
      .values(insertLog)
      .returning();
    return log;
  }

  async getLogs(automationId: number): Promise<AutomationLog[]> {
    return db
      .select()
      .from(automationLogs)
      .where(eq(automationLogs.automationId, automationId))
      .orderBy(automationLogs.timestamp);
  }
}

export const storage = new DatabaseStorage();
