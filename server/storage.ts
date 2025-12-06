import { type AutomationTask, type BrowserAction } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  createTask(prompt: string): Promise<AutomationTask>;
  getTask(id: string): Promise<AutomationTask | undefined>;
  updateTask(id: string, updates: Partial<AutomationTask>): Promise<AutomationTask | undefined>;
  addAction(taskId: string, action: Omit<BrowserAction, "id">): Promise<BrowserAction | undefined>;
  updateAction(taskId: string, actionId: string, updates: Partial<BrowserAction>): Promise<BrowserAction | undefined>;
  getAllTasks(): Promise<AutomationTask[]>;
  clearTasks(): Promise<void>;
}

export class MemStorage implements IStorage {
  private tasks: Map<string, AutomationTask>;

  constructor() {
    this.tasks = new Map();
  }

  async createTask(prompt: string): Promise<AutomationTask> {
    const id = randomUUID();
    const task: AutomationTask = {
      id,
      prompt,
      status: "pending",
      actions: [],
      createdAt: Date.now(),
    };
    this.tasks.set(id, task);
    return task;
  }

  async getTask(id: string): Promise<AutomationTask | undefined> {
    return this.tasks.get(id);
  }

  async updateTask(id: string, updates: Partial<AutomationTask>): Promise<AutomationTask | undefined> {
    const task = this.tasks.get(id);
    if (!task) return undefined;
    
    const updated = { ...task, ...updates };
    this.tasks.set(id, updated);
    return updated;
  }

  async addAction(taskId: string, action: Omit<BrowserAction, "id">): Promise<BrowserAction | undefined> {
    const task = this.tasks.get(taskId);
    if (!task) return undefined;

    const actionWithId: BrowserAction = {
      ...action,
      id: randomUUID(),
    };
    
    task.actions.push(actionWithId);
    this.tasks.set(taskId, task);
    return actionWithId;
  }

  async updateAction(taskId: string, actionId: string, updates: Partial<BrowserAction>): Promise<BrowserAction | undefined> {
    const task = this.tasks.get(taskId);
    if (!task) return undefined;

    const actionIndex = task.actions.findIndex((a) => a.id === actionId);
    if (actionIndex === -1) return undefined;

    task.actions[actionIndex] = { ...task.actions[actionIndex], ...updates };
    this.tasks.set(taskId, task);
    return task.actions[actionIndex];
  }

  async getAllTasks(): Promise<AutomationTask[]> {
    return Array.from(this.tasks.values()).sort((a, b) => b.createdAt - a.createdAt);
  }

  async clearTasks(): Promise<void> {
    this.tasks.clear();
  }
}

export const storage = new MemStorage();
