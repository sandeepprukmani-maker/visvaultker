tegrating withimport { chromium, type Browser, type Page, type BrowserContext } from "playwright";
import type { AutomationStep } from "./openai";
import type { InsertAutomationLog } from "@shared/schema";
import { openAIService } from "./openai";

export interface ExecutionResult {
  success: boolean;
  duration: number;
  logs: InsertAutomationLog[];
  error?: string;
  data?: any;
}

export interface AutomationOptions {
  maxRetries?: number;
  retryDelay?: number;
  screenshot?: boolean;
  cookies?: any[];
  localStorage?: Record<string, string>;
  sessionStorage?: Record<string, string>;
  proxy?: {
    server: string;
    username?: string;
    password?: string;
  };
  headless?: boolean;
}

export class AutomationService {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private currentProxy: string | null = null;
  private currentHeadless: boolean = true;

  async initialize(options: AutomationOptions = {}) {
    const headless = options.headless !== false;
    const newProxy = options.proxy ? JSON.stringify(options.proxy) : null;
    const proxyChanged = this.currentProxy !== newProxy;
    const headlessChanged = this.currentHeadless !== headless;

    if (proxyChanged || headlessChanged || !this.browser) {
      await this.close();
      
      const launchOptions: any = {
        headless,
        args: [
          '--disable-blink-features=AutomationControlled',
          '--disable-dev-shm-usage',
          '--no-sandbox',
        ],
      };

      if (options.proxy) {
        launchOptions.proxy = options.proxy;
      }

      this.browser = await chromium.launch(launchOptions);
      this.currentProxy = newProxy;
      this.currentHeadless = headless;
    }

    if (this.context) {
      await this.context.close();
    }

    const contextOptions: any = {
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      ignoreHTTPSErrors: true,
    };

    this.context = await this.browser.newContext(contextOptions);

    if (options.cookies && options.cookies.length > 0) {
      await this.context.addCookies(options.cookies);
    }

    await this.context.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
      });
    });
  }

  async close() {
    if (this.context) {
      await this.context.close();
      this.context = null;
    }
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async executeAutomation(
    automationId: string,
    steps: AutomationStep[],
    options: AutomationOptions & { baseUrl?: string } = {}
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const logs: InsertAutomationLog[] = [];
    let extractedData: any = {};

    await this.initialize(options);
    const page = await this.context!.newPage();

    if (options.localStorage) {
      await page.addInitScript((storage) => {
        Object.entries(storage).forEach(([key, value]) => {
          localStorage.setItem(key, value);
        });
      }, options.localStorage);
    }

    if (options.sessionStorage) {
      await page.addInitScript((storage) => {
        Object.entries(storage).forEach(([key, value]) => {
          sessionStorage.setItem(key, value);
        });
      }, options.sessionStorage);
    }

    try {
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        const stepStart = Date.now();
        let status = "success";
        let details: string | undefined;

        if (step.waitBefore) {
          await page.waitForTimeout(step.waitBefore);
        }

        try {
          const result = await this.executeStepWithRetry(page, step, options);
          
          if (result && typeof result === 'object') {
            extractedData = { ...extractedData, ...result };
          }

          if (options.screenshot || ["click", "navigate", "verify"].includes(step.action)) {
            const screenshot = await page.screenshot({
              type: "jpeg",
              quality: 70,
            });
            details = `data:image/jpeg;base64,${screenshot.toString("base64")}`;
          }
        } catch (error) {
          status = "error";
          details = error instanceof Error ? error.message : String(error);
        }

        logs.push({
          automationId,
          action: step.description,
          status,
          details,
          screenshot: details && details.startsWith("data:image") ? details : undefined,
        });

        if (status === "error") {
          throw new Error(`Step ${i + 1} failed: ${step.description}`);
        }
      }

      const duration = Date.now() - startTime;
      await page.close();

      return {
        success: true,
        duration,
        logs,
        data: Object.keys(extractedData).length > 0 ? extractedData : undefined,
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      await page.close();

      return {
        success: false,
        duration,
        logs,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private async executeStepWithRetry(
    page: Page,
    step: AutomationStep,
    options: AutomationOptions & { baseUrl?: string }
  ): Promise<any> {
    const maxRetries = step.retryCount !== undefined ? step.retryCount : (options.maxRetries || 3);
    const retryDelay = options.retryDelay || 1000;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          await page.waitForTimeout(retryDelay * Math.pow(2, attempt - 1));
        }
        
        return await this.executeStep(page, step, options);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        if (attempt < maxRetries && step.fallbackSelectors && step.fallbackSelectors.length > 0) {
          const originalSelector = step.selector;
          step.selector = step.fallbackSelectors[attempt % step.fallbackSelectors.length];
          console.log(`Retrying with fallback selector: ${step.selector}`);
        } else if (attempt < maxRetries) {
          console.log(`Retry attempt ${attempt + 1}/${maxRetries} for: ${step.description}`);
        }
      }
    }

    throw lastError;
  }

  private async executeStep(
    page: Page,
    step: AutomationStep,
    options: { baseUrl?: string }
  ): Promise<any> {
    switch (step.action) {
      case "navigate":
        if (step.value) {
          const url = step.value.startsWith("http")
            ? step.value
            : `${options.baseUrl || ""}${step.value}`;
          await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
          await page.waitForTimeout(1000);
        }
        break;

      case "click":
        if (step.selector) {
          const element = await this.findElementWithFallback(page, step);
          if (!element) {
            throw new Error(`Element not found: ${step.selector}`);
          }
          await element.click();
          await page.waitForTimeout(500);
        }
        break;

      case "type":
        if (step.selector && step.value !== undefined) {
          const element = await this.findElementWithFallback(page, step);
          if (!element) {
            throw new Error(`Element not found: ${step.selector}`);
          }
          await element.fill(step.value);
          await page.waitForTimeout(300);
        }
        break;

      case "select":
        if (step.selector && step.value !== undefined) {
          const element = await this.findElementWithFallback(page, step);
          if (!element) {
            throw new Error(`Element not found: ${step.selector}`);
          }
          await element.selectOption(step.value);
          await page.waitForTimeout(300);
        }
        break;

      case "wait":
        const waitTime = parseInt(step.value || "1000", 10);
        await page.waitForTimeout(waitTime);
        break;

      case "waitForElement":
        if (step.selector) {
          await page.waitForSelector(step.selector, { 
            timeout: step.value ? parseInt(step.value, 10) : 10000,
            state: 'visible',
          });
        }
        break;

      case "scroll":
        if (step.selector) {
          const element = await page.$(step.selector);
          if (element) {
            await element.scrollIntoViewIfNeeded();
          }
        } else if (step.value) {
          const scrollAmount = parseInt(step.value, 10);
          await page.evaluate((amount) => window.scrollBy(0, amount), scrollAmount);
        }
        await page.waitForTimeout(300);
        break;

      case "hover":
        if (step.selector) {
          const element = await this.findElementWithFallback(page, step);
          if (!element) {
            throw new Error(`Element not found: ${step.selector}`);
          }
          await element.hover();
          await page.waitForTimeout(300);
        }
        break;

      case "pressKey":
        if (step.value) {
          await page.keyboard.press(step.value);
          await page.waitForTimeout(200);
        }
        break;

      case "extract":
        if (step.selector) {
          return await this.extractData(page, step);
        }
        break;

      case "extractTable":
        if (step.selector) {
          return await this.extractTableData(page, step.selector);
        }
        break;

      case "verify":
        if (step.selector) {
          const element = await this.findElementWithFallback(page, step);
          if (!element) {
            throw new Error(`Verification failed: ${step.selector} not found`);
          }
          if (step.value) {
            const text = await element.textContent();
            if (!text?.includes(step.value)) {
              throw new Error(
                `Verification failed: Expected text "${step.value}" not found`
              );
            }
          }
        }
        break;

      case "screenshot":
        const screenshot = await page.screenshot({
          type: "jpeg",
          quality: 80,
          fullPage: step.value === "fullPage",
        });
        return { screenshot: `data:image/jpeg;base64,${screenshot.toString("base64")}` };

      default:
        console.warn(`Unknown action: ${step.action}`);
    }

    return null;
  }

  private async findElementWithFallback(page: Page, step: AutomationStep): Promise<any> {
    const selectors = [
      step.selector,
      step.xpath,
      step.textSelector,
      ...(step.fallbackSelectors || []),
    ].filter(Boolean) as string[];

    for (const selector of selectors) {
      try {
        if (selector.startsWith('//') || selector.startsWith('(//')) {
          await page.waitForSelector(`xpath=${selector}`, { timeout: 5000, state: 'visible' });
          const element = await page.$(`xpath=${selector}`);
          if (element) return element;
        } else if (selector.startsWith('text=')) {
          const text = selector.replace('text=', '').replace(/"/g, '');
          await page.waitForSelector(`text=${text}`, { timeout: 5000, state: 'visible' });
          const element = await page.$(`text=${text}`);
          if (element) return element;
        } else {
          await page.waitForSelector(selector, { timeout: 5000, state: 'visible' });
          const element = await page.$(selector);
          if (element) return element;
        }
      } catch (error) {
        console.log(`Selector failed: ${selector}, trying next...`);
        continue;
      }
    }

    return null;
  }

  private async extractData(page: Page, step: AutomationStep): Promise<any> {
    try {
      if (!step.selector) return null;

      const elements = await page.$$(step.selector);
      const data = [];

      for (const element of elements) {
        const text = await element.textContent();
        const value = await element.evaluate((el: any) => el.value);
        const attributes = await element.evaluate((el) => {
          const attrs: Record<string, string> = {};
          const attrArray = Array.from((el as Element).attributes);
          for (const attr of attrArray) {
            attrs[attr.name] = attr.value;
          }
          return attrs;
        });

        data.push({
          text: text?.trim(),
          value,
          attributes,
        });
      }

      return { [step.value || 'extracted']: data };
    } catch (error) {
      console.error('Error extracting data:', error);
      return null;
    }
  }

  private async extractTableData(page: Page, selector: string): Promise<any> {
    try {
      const tableData = await page.evaluate((sel) => {
        const table = document.querySelector(sel);
        if (!table) return null;

        const headers: string[] = [];
        const rows: any[] = [];

        const headerCells = table.querySelectorAll('thead th, thead td');
        headerCells.forEach((cell) => {
          headers.push(cell.textContent?.trim() || '');
        });

        const bodyRows = table.querySelectorAll('tbody tr');
        bodyRows.forEach((row) => {
          const rowData: Record<string, string> = {};
          const cells = row.querySelectorAll('td, th');
          cells.forEach((cell, index) => {
            const header = headers[index] || `column_${index}`;
            rowData[header] = cell.textContent?.trim() || '';
          });
          rows.push(rowData);
        });

        return { headers, rows };
      }, selector);

      return { tableData };
    } catch (error) {
      console.error('Error extracting table:', error);
      return null;
    }
  }

  async testSelector(url: string, selector: string): Promise<boolean> {
    await this.initialize();
    const page = await this.context!.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
      const element = await page.$(selector);
      await page.close();
      return element !== null;
    } catch (error) {
      await page.close();
      return false;
    }
  }

  async recordActions(url: string, duration: number = 60000): Promise<AutomationStep[]> {
    await this.initialize();
    const page = await this.context!.newPage();
    const recordedActions: AutomationStep[] = [];

    await page.goto(url);

    await page.exposeFunction('recordClick', async (selector: string, text: string) => {
      recordedActions.push({
        action: 'click',
        selector,
        description: `Click on "${text || selector}"`,
      });
    });

    await page.exposeFunction('recordType', async (selector: string, value: string) => {
      recordedActions.push({
        action: 'type',
        selector,
        value,
        description: `Type "${value}" into ${selector}`,
      });
    });

    await page.evaluate(() => {
      document.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const selector = target.id 
          ? `#${target.id}` 
          : target.getAttribute('data-testid')
          ? `[data-testid="${target.getAttribute('data-testid')}"]`
          : target.tagName.toLowerCase();
        (window as any).recordClick(selector, target.textContent?.trim());
      });

      document.addEventListener('input', (e) => {
        const target = e.target as HTMLInputElement;
        const selector = target.id 
          ? `#${target.id}` 
          : target.getAttribute('name')
          ? `[name="${target.getAttribute('name')}"]`
          : 'input';
        (window as any).recordType(selector, target.value);
      });
    });

    await page.waitForTimeout(duration);
    await page.close();

    return recordedActions;
  }

  async getCookies(): Promise<any[]> {
    if (this.context) {
      return await this.context.cookies();
    }
    return [];
  }

  async getLocalStorage(url: string): Promise<Record<string, string>> {
    if (!this.context) return {};
    
    const page = await this.context.newPage();
    try {
      await page.goto(url);
      const storage = await page.evaluate(() => {
        const items: Record<string, string> = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key) {
            items[key] = localStorage.getItem(key) || '';
          }
        }
        return items;
      });
      return storage;
    } finally {
      await page.close();
    }
  }
}

export const automationService = new AutomationService();
