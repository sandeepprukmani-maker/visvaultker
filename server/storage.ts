import { db } from "./db";
import {
  scenarios,
  type InsertScenario,
  type Scenario
} from "@shared/schema";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  // Scenarios (Persisted)
  createScenario(scenario: InsertScenario): Promise<Scenario>;
  getScenarios(): Promise<Scenario[]>;
  getScenario(id: number): Promise<Scenario | undefined>;
  deleteScenario(id: number): Promise<void>;
}

export class DatabaseStorage implements IStorage {
  async createScenario(scenario: InsertScenario): Promise<Scenario> {
    const [created] = await db.insert(scenarios).values(scenario).returning();
    return created;
  }

  async getScenarios(): Promise<Scenario[]> {
    // Limit to 100 as per spec description "up to 100... in past 30 days"
    return await db.select()
      .from(scenarios)
      .orderBy(desc(scenarios.createdAt))
      .limit(100);
  }

  async getScenario(id: number): Promise<Scenario | undefined> {
    const [scenario] = await db.select().from(scenarios).where(eq(scenarios.id, id));
    return scenario;
  }

  async deleteScenario(id: number): Promise<void> {
    await db.delete(scenarios).where(eq(scenarios.id, id));
  }
}

export const storage = new DatabaseStorage();
