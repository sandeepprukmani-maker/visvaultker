import {
  type CrawlSession,
  type InsertCrawlSession,
  type Page,
  type InsertPage,
  type Element,
  type InsertElement,
  type Automation,
  type InsertAutomation,
  type AutomationLog,
  type InsertAutomationLog,
  crawlSessions,
  pages,
  elements,
  automations,
  automationLogs,
} from "@shared/schema";
import { drizzle } from "drizzle-orm/neon-serverless";
import { Pool } from "@neondatabase/serverless";
import { eq, desc, or, like } from "drizzle-orm";

export interface AppSettings {
  apiKey?: string;
  autoScreenshots: boolean;
  templateDetection: boolean;
  parallelCrawling: boolean;
  selfHealing: boolean;
  learningFromFailures: boolean;
}

export interface IStorage {
  // Crawl Sessions
  createCrawlSession(session: InsertCrawlSession): Promise<CrawlSession>;
  getCrawlSession(id: string): Promise<CrawlSession | undefined>;
  updateCrawlSession(id: string, updates: Partial<CrawlSession>): Promise<CrawlSession | undefined>;
  getAllCrawlSessions(): Promise<CrawlSession[]>;

  // Pages
  createPage(page: InsertPage): Promise<Page>;
  getPage(id: string): Promise<Page | undefined>;
  getPagesBySession(sessionId: string): Promise<Page[]>;
  getAllPages(): Promise<Page[]>;

  // Elements
  createElement(element: InsertElement): Promise<Element>;
  getElement(id: string): Promise<Element | undefined>;
  getElementsByPage(pageId: string): Promise<Element[]>;
  searchElements(query: string): Promise<Element[]>;

  // Automations
  createAutomation(automation: InsertAutomation): Promise<Automation>;
  getAutomation(id: string): Promise<Automation | undefined>;
  updateAutomation(id: string, updates: Partial<Automation>): Promise<Automation | undefined>;
  getAllAutomations(): Promise<Automation[]>;

  // Automation Logs
  createAutomationLog(log: InsertAutomationLog): Promise<AutomationLog>;
  getAutomationLogs(automationId: string): Promise<AutomationLog[]>;

  // Settings
  getSettings(): Promise<AppSettings>;
  updateSettings(settings: Partial<AppSettings>): Promise<AppSettings>;
}

const pool = new Pool({ connectionString: process.env.DATABASE_URL! });
const db = drizzle(pool);

export class DbStorage implements IStorage {
  private settings: AppSettings = {
    autoScreenshots: true,
    templateDetection: true,
    parallelCrawling: true,
    selfHealing: true,
    learningFromFailures: true,
  };

  // Crawl Sessions
  async createCrawlSession(insertSession: InsertCrawlSession): Promise<CrawlSession> {
    const id = randomUUID();
    const session: CrawlSession = {
      id,
      url: insertSession.url,
      depth: insertSession.depth ?? 3,
      status: "pending",
      pagesFound: 0,
      elementsFound: 0,
      startedAt: new Date(),
      completedAt: null,
    };
    this.crawlSessions.set(id, session);
    return session;
  }

  async getCrawlSession(id: string): Promise<CrawlSession | undefined> {
    return this.crawlSessions.get(id);
  }

  async updateCrawlSession(id: string, updates: Partial<CrawlSession>): Promise<CrawlSession | undefined> {
    const session = this.crawlSessions.get(id);
    if (!session) return undefined;
    const updated = { ...session, ...updates };
    this.crawlSessions.set(id, updated);
    return updated;
  }

  async getAllCrawlSessions(): Promise<CrawlSession[]> {
    return Array.from(this.crawlSessions.values()).sort(
      (a, b) => b.startedAt.getTime() - a.startedAt.getTime()
    );
  }

  // Pages
  async createPage(insertPage: InsertPage): Promise<Page> {
    const id = randomUUID();
    const page: Page = {
      id,
      crawlSessionId: insertPage.crawlSessionId,
      url: insertPage.url,
      title: insertPage.title,
      elementCount: insertPage.elementCount ?? 0,
      screenshot: insertPage.screenshot ?? null,
      templateHash: insertPage.templateHash ?? null,
      templateGroup: insertPage.templateGroup ?? null,
      crawledAt: new Date(),
    };
    this.pages.set(id, page);
    return page;
  }

  async getPage(id: string): Promise<Page | undefined> {
    return this.pages.get(id);
  }

  async getPagesBySession(sessionId: string): Promise<Page[]> {
    return Array.from(this.pages.values()).filter(
      (page) => page.crawlSessionId === sessionId
    );
  }

  async getAllPages(): Promise<Page[]> {
    return Array.from(this.pages.values()).sort(
      (a, b) => b.crawledAt.getTime() - a.crawledAt.getTime()
    );
  }

  // Elements
  async createElement(insertElement: InsertElement): Promise<Element> {
    const id = randomUUID();
    const element: Element = {
      id,
      pageId: insertElement.pageId,
      tag: insertElement.tag,
      selector: insertElement.selector,
      text: insertElement.text ?? null,
      attributes: insertElement.attributes ?? {},
      xpath: insertElement.xpath ?? null,
      confidence: insertElement.confidence ?? 100,
      embedding: insertElement.embedding ?? null,
    };
    this.elements.set(id, element);
    return element;
  }

  async getElement(id: string): Promise<Element | undefined> {
    return this.elements.get(id);
  }

  async getElementsByPage(pageId: string): Promise<Element[]> {
    return Array.from(this.elements.values()).filter(
      (element) => element.pageId === pageId
    );
  }

  async searchElements(query: string): Promise<Element[]> {
    const lowerQuery = query.toLowerCase();
    return Array.from(this.elements.values()).filter(
      (element) =>
        element.tag.toLowerCase().includes(lowerQuery) ||
        element.selector.toLowerCase().includes(lowerQuery) ||
        (element.text && element.text.toLowerCase().includes(lowerQuery))
    );
  }

  // Automations
  async createAutomation(insertAutomation: InsertAutomation): Promise<Automation> {
    const id = randomUUID();
    const automation: Automation = {
      id,
      command: insertAutomation.command,
      status: "queued",
      plan: insertAutomation.plan ?? null,
      result: insertAutomation.result ?? null,
      duration: null,
      actionCount: 0,
      createdAt: new Date(),
      completedAt: null,
    };
    this.automations.set(id, automation);
    return automation;
  }

  async getAutomation(id: string): Promise<Automation | undefined> {
    return this.automations.get(id);
  }

  async updateAutomation(id: string, updates: Partial<Automation>): Promise<Automation | undefined> {
    const automation = this.automations.get(id);
    if (!automation) return undefined;
    const updated = { ...automation, ...updates };
    this.automations.set(id, updated);
    return updated;
  }

  async getAllAutomations(): Promise<Automation[]> {
    return Array.from(this.automations.values()).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime()
    );
  }

  // Automation Logs
  async createAutomationLog(insertLog: InsertAutomationLog): Promise<AutomationLog> {
    const id = randomUUID();
    const log: AutomationLog = {
      id,
      automationId: insertLog.automationId,
      timestamp: new Date(),
      action: insertLog.action,
      status: insertLog.status,
      details: insertLog.details ?? null,
      screenshot: insertLog.screenshot ?? null,
    };
    this.automationLogs.set(id, log);
    return log;
  }

  async getAutomationLogs(automationId: string): Promise<AutomationLog[]> {
    return Array.from(this.automationLogs.values())
      .filter((log) => log.automationId === automationId)
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }

  async getSettings(): Promise<AppSettings> {
    return { ...this.settings };
  }

  async updateSettings(updates: Partial<AppSettings>): Promise<AppSettings> {
    this.settings = { ...this.settings, ...updates };
    return { ...this.settings };
  }
}

export const storage = new MemStorage();
