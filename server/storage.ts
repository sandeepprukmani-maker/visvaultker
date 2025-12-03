import { type User, type InsertUser, type Execution, type InsertExecution, type Workflow, type LogEntry } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  getExecutions(): Promise<Execution[]>;
  getExecution(id: string): Promise<Execution | undefined>;
  createExecution(execution: InsertExecution): Promise<Execution>;
  updateExecution(id: string, updates: Partial<Execution>): Promise<Execution | undefined>;
  deleteExecution(id: string): Promise<boolean>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private executions: Map<string, Execution>;

  constructor() {
    this.users = new Map();
    this.executions = new Map();
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async getExecutions(): Promise<Execution[]> {
    return Array.from(this.executions.values()).sort((a, b) => {
      const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
      const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
      return dateB - dateA;
    });
  }

  async getExecution(id: string): Promise<Execution | undefined> {
    return this.executions.get(id);
  }

  async createExecution(insertExecution: InsertExecution): Promise<Execution> {
    const id = randomUUID();
    const execution: Execution = {
      id,
      prompt: insertExecution.prompt,
      status: insertExecution.status || "planning",
      workflow: insertExecution.workflow || null,
      logs: insertExecution.logs || [],
      result: insertExecution.result || null,
      error: insertExecution.error || null,
      progress: insertExecution.progress || 0,
      currentStep: insertExecution.currentStep || null,
      createdAt: new Date(),
      completedAt: null,
    };
    this.executions.set(id, execution);
    return execution;
  }

  async updateExecution(id: string, updates: Partial<Execution>): Promise<Execution | undefined> {
    const execution = this.executions.get(id);
    if (!execution) return undefined;
    
    const updated = { ...execution, ...updates };
    this.executions.set(id, updated);
    return updated;
  }

  async deleteExecution(id: string): Promise<boolean> {
    return this.executions.delete(id);
  }
}

export const storage = new MemStorage();
