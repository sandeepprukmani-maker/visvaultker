import { chromium, type Browser, type Page } from "playwright";
import type { AutomationStep } from "./openai";
import type { InsertAutomationLog } from "@shared/schema";

export interface ExecutionResult {
  success: boolean;
  duration: number;
  logs: InsertAutomationLog[];
  error?: string;
}

export class AutomationService {
  private browser: Browser | null = null;

  async initialize() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
      });
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Execute an automation plan
   */
  async executeAutomation(
    automationId: string,
    steps: AutomationStep[],
    baseUrl?: string
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const logs: InsertAutomationLog[] = [];

    await this.initialize();
    const page = await this.browser!.newPage();

    try {
      for (const step of steps) {
        const stepStart = Date.now();
        let status = "success";
        let details: string | undefined;

        try {
          await this.executeStep(page, step, baseUrl);

          // Capture screenshot after important actions
          if (["click", "navigate", "verify"].includes(step.action)) {
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
          throw new Error(`Step failed: ${step.description}`);
        }
      }

      const duration = Date.now() - startTime;
      await page.close();

      return {
        success: true,
        duration,
        logs,
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

  /**
   * Execute a single automation step
   */
  private async executeStep(
    page: Page,
    step: AutomationStep,
    baseUrl?: string
  ): Promise<void> {
    switch (step.action) {
      case "navigate":
        if (step.value) {
          const url = step.value.startsWith("http")
            ? step.value
            : `${baseUrl || ""}${step.value}`;
          await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
          await page.waitForTimeout(1000);
        }
        break;

      case "click":
        if (step.selector) {
          await page.waitForSelector(step.selector, { timeout: 10000 });
          await page.click(step.selector);
          await page.waitForTimeout(500);
        }
        break;

      case "type":
        if (step.selector && step.value !== undefined) {
          await page.waitForSelector(step.selector, { timeout: 10000 });
          await page.fill(step.selector, step.value);
          await page.waitForTimeout(300);
        }
        break;

      case "select":
        if (step.selector && step.value !== undefined) {
          await page.waitForSelector(step.selector, { timeout: 10000 });
          await page.selectOption(step.selector, step.value);
          await page.waitForTimeout(300);
        }
        break;

      case "wait":
        const waitTime = parseInt(step.value || "1000", 10);
        await page.waitForTimeout(waitTime);
        break;

      case "verify":
        if (step.selector) {
          await page.waitForSelector(step.selector, { timeout: 10000 });
          const element = await page.$(step.selector);
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

      default:
        console.warn(`Unknown action: ${step.action}`);
    }
  }

  /**
   * Test a selector on a page to verify it exists
   */
  async testSelector(url: string, selector: string): Promise<boolean> {
    await this.initialize();
    const page = await this.browser!.newPage();

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
}

export const automationService = new AutomationService();
