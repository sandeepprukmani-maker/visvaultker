import {
  type AutomationHistory,
  type InsertAutomationHistory,
  type AutomationTemplate,
  type InsertAutomationTemplate,
  type TokenMetrics,
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Automation History
  getAutomationHistory(id: string): Promise<AutomationHistory | undefined>;
  getAllAutomationHistory(): Promise<AutomationHistory[]>;
  createAutomationHistory(history: InsertAutomationHistory): Promise<AutomationHistory>;
  
  // Templates
  getTemplate(id: string): Promise<AutomationTemplate | undefined>;
  getAllTemplates(): Promise<AutomationTemplate[]>;
  createTemplate(template: InsertAutomationTemplate): Promise<AutomationTemplate>;
  
  // Metrics
  getTokenMetrics(): Promise<TokenMetrics>;
}

export class MemStorage implements IStorage {
  private automationHistory: Map<string, AutomationHistory>;
  private templates: Map<string, AutomationTemplate>;

  constructor() {
    this.automationHistory = new Map();
    this.templates = new Map();
    
    // Initialize with default templates
    this.initializeDefaultTemplates();
  }

  private async initializeDefaultTemplates() {
    const defaultTemplates: InsertAutomationTemplate[] = [
      {
        name: "Navigate to Website",
        description: "Open a specific URL in the browser",
        prompt: "Go to example.com",
        category: "navigation",
        icon: "Globe",
      },
      {
        name: "Fill Form",
        description: "Automatically fill out web forms",
        prompt: "Fill the contact form with name 'John Doe' and email 'john@example.com'",
        category: "form",
        icon: "FileText",
      },
      {
        name: "Extract Data",
        description: "Scrape data from web pages",
        prompt: "Extract all product names and prices from the page",
        category: "extraction",
        icon: "Database",
      },
      {
        name: "Test Flow",
        description: "Test a complete user journey",
        prompt: "Test the login flow with username 'test' and password 'demo123'",
        category: "testing",
        icon: "TestTube2",
      },
    ];

    for (const template of defaultTemplates) {
      await this.createTemplate(template);
    }
  }

  // Automation History methods
  async getAutomationHistory(id: string): Promise<AutomationHistory | undefined> {
    return this.automationHistory.get(id);
  }

  async getAllAutomationHistory(): Promise<AutomationHistory[]> {
    return Array.from(this.automationHistory.values())
      .sort((a, b) => {
        const aTime = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const bTime = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return bTime - aTime; // Most recent first
      });
  }

  async createAutomationHistory(insertHistory: InsertAutomationHistory): Promise<AutomationHistory> {
    const id = randomUUID();
    const history: AutomationHistory = {
      ...insertHistory,
      id,
      createdAt: new Date(),
    };
    this.automationHistory.set(id, history);
    return history;
  }

  // Template methods
  async getTemplate(id: string): Promise<AutomationTemplate | undefined> {
    return this.templates.get(id);
  }

  async getAllTemplates(): Promise<AutomationTemplate[]> {
    return Array.from(this.templates.values());
  }

  async createTemplate(insertTemplate: InsertAutomationTemplate): Promise<AutomationTemplate> {
    const id = randomUUID();
    const template: AutomationTemplate = {
      ...insertTemplate,
      id,
    };
    this.templates.set(id, template);
    return template;
  }

  // Metrics methods
  async getTokenMetrics(): Promise<TokenMetrics> {
    const allHistory = await this.getAllAutomationHistory();
    const successfulExecutions = allHistory.filter(h => h.status === 'success');
    
    const totalTokensUsed = successfulExecutions.reduce((sum, h) => sum + (h.tokensUsed || 0), 0);
    const totalExecutions = successfulExecutions.length;
    const averageTokensPerExecution = totalExecutions > 0 ? totalTokensUsed / totalExecutions : 0;
    const averageExecutionTime = totalExecutions > 0
      ? successfulExecutions.reduce((sum, h) => sum + (h.executionTime || 0), 0) / totalExecutions
      : 0;
    
    // Estimated savings calculation (assuming unoptimized would use ~5x more tokens)
    const estimatedSavings = 78; // Hardcoded for now, could be calculated based on prompt caching effectiveness
    
    return {
      totalTokensUsed,
      totalExecutions,
      averageTokensPerExecution: Math.round(averageTokensPerExecution),
      estimatedSavings,
      averageExecutionTime: Math.round(averageExecutionTime),
    };
  }
}

export const storage = new MemStorage();
