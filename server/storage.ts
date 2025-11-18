import {
  type Automation,
  type InsertAutomation,
  type Cache,
  type InsertCache,
  type Settings,
  type InsertSettings,
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Automations
  getAutomation(id: string): Promise<Automation | undefined>;
  getAllAutomations(): Promise<Automation[]>;
  createAutomation(automation: InsertAutomation): Promise<Automation>;
  updateAutomation(id: string, updates: Partial<Automation>): Promise<Automation | undefined>;
  deleteAutomation(id: string): Promise<boolean>;

  // Cache
  getCachedPattern(id: string): Promise<Cache | undefined>;
  getAllCachedPatterns(): Promise<Cache[]>;
  createCachedPattern(cache: InsertCache): Promise<Cache>;
  updateCachedPattern(id: string, updates: Partial<Cache>): Promise<Cache | undefined>;
  
  // Settings
  getSettings(): Promise<Settings | undefined>;
  updateSettings(settings: Partial<Settings>): Promise<Settings>;
}

export class MemStorage implements IStorage {
  private automations: Map<string, Automation>;
  private cache: Map<string, Cache>;
  private settings: Settings;

  constructor() {
    this.automations = new Map();
    this.cache = new Map();
    this.settings = {
      id: randomUUID(),
      selectedModel: "openai",
      theme: "light",
      updatedAt: new Date(),
    };
  }

  // Automations
  async getAutomation(id: string): Promise<Automation | undefined> {
    return this.automations.get(id);
  }

  async getAllAutomations(): Promise<Automation[]> {
    return Array.from(this.automations.values()).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }

  async createAutomation(insertAutomation: InsertAutomation): Promise<Automation> {
    const id = randomUUID();
    const automation: Automation = {
      ...insertAutomation,
      id,
      createdAt: new Date(),
    };
    this.automations.set(id, automation);
    return automation;
  }

  async updateAutomation(id: string, updates: Partial<Automation>): Promise<Automation | undefined> {
    const automation = this.automations.get(id);
    if (!automation) return undefined;
    
    const updated = { ...automation, ...updates };
    this.automations.set(id, updated);
    return updated;
  }

  async deleteAutomation(id: string): Promise<boolean> {
    return this.automations.delete(id);
  }

  // Cache
  async getCachedPattern(id: string): Promise<Cache | undefined> {
    return this.cache.get(id);
  }

  async getAllCachedPatterns(): Promise<Cache[]> {
    return Array.from(this.cache.values()).sort(
      (a, b) => new Date(b.lastUsed).getTime() - new Date(a.lastUsed).getTime()
    );
  }

  async createCachedPattern(insertCache: InsertCache): Promise<Cache> {
    const id = randomUUID();
    const cache: Cache = {
      ...insertCache,
      id,
      lastUsed: new Date(),
      createdAt: new Date(),
    };
    this.cache.set(id, cache);
    return cache;
  }

  async updateCachedPattern(id: string, updates: Partial<Cache>): Promise<Cache | undefined> {
    const cachedPattern = this.cache.get(id);
    if (!cachedPattern) return undefined;
    
    const updated = { ...cachedPattern, ...updates, lastUsed: new Date() };
    this.cache.set(id, updated);
    return updated;
  }

  // Settings
  async getSettings(): Promise<Settings | undefined> {
    return this.settings;
  }

  async updateSettings(updates: Partial<Settings>): Promise<Settings> {
    this.settings = {
      ...this.settings,
      ...updates,
      updatedAt: new Date(),
    };
    return this.settings;
  }
}

export const storage = new MemStorage();
