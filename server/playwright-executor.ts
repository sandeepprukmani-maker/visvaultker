import { chromium, type Browser, type Page, type BrowserContext } from "@playwright/test";

export interface ExecutionResult {
  success: boolean;
  result: string;
  executedCode: string;
  pageState: string;
  error?: string;
}

/**
 * PlaywrightExecutor manages browser instances and executes automation actions
 * Uses headed mode by default for visibility (as per Playwright MCP design)
 */
export class PlaywrightExecutor {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  async initialize() {
    if (this.browser) {
      return; // Already initialized
    }

    // Launch browser in headless mode for server environment
    // Headless mode works in containerized environments like Replit
    this.browser = await chromium.launch({
      headless: false,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    });

    this.context = await this.browser.newContext({
      viewport: { width: 1280, height: 720 },
    });

    this.page = await this.context.newPage();
  }

  async executeAction(code: string, description: string): Promise<ExecutionResult> {
    try {
      await this.initialize();

      if (!this.page) {
        throw new Error("Browser page not initialized");
      }

      // Safe execution of Playwright code by parsing and executing allowed actions
      // This avoids eval() security issues while still allowing dynamic automation
      await this.executeSafePlaywrightCode(code);

      // Get page state after execution
      const pageState = await this.getPageState();

      return {
        success: true,
        result: `Successfully executed: ${description}`,
        executedCode: code,
        pageState,
      };
    } catch (error) {
      console.error("Execution error:", error);
      return {
        success: false,
        result: `Failed to execute: ${description}`,
        executedCode: code,
        pageState: await this.getPageState(),
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private async executeSafePlaywrightCode(code: string): Promise<void> {
    if (!this.page) {
      throw new Error("Browser page not initialized");
    }

    const page = this.page;

    // Parse and execute allowed Playwright commands
    // This is safer than eval() but still allows dynamic automation
    const lines = code.split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('//'));
    
    for (const line of lines) {
      // Remove "await " and "page." prefixes for parsing
      let command = line.replace(/^await\s+/, '').replace(/^page\./, '').replace(/;$/, '');
      
      // Execute common Playwright commands safely
      if (command.startsWith('goto(')) {
        const url = command.match(/goto\(['"](.+?)['"]\)/)?.[1];
        if (url) await page.goto(url);
      } else if (command.startsWith('click(')) {
        const selector = this.extractSelector(command);
        if (selector) await page.locator(selector).click();
      } else if (command.startsWith('fill(')) {
        const match = command.match(/fill\((.+?),\s*['"](.+?)['"]\)/);
        if (match) {
          const selector = this.extractSelector(match[1]);
          const value = match[2];
          if (selector) await page.locator(selector).fill(value);
        }
      } else if (command.startsWith('getByRole(')) {
        // Handle getByRole selectors with click/fill
        if (command.includes('.click()')) {
          const match = command.match(/getByRole\(['"](.+?)['"],\s*\{.*?name:\s*['"](.+?)['"]/);
          if (match) await page.getByRole(match[1] as any, { name: match[2] }).click();
        } else if (command.includes('.fill(')) {
          const roleMatch = command.match(/getByRole\(['"](.+?)['"],\s*\{.*?name:\s*['"](.+?)['"]/);
          const fillMatch = command.match(/\.fill\(['"](.+?)['"]\)/);
          if (roleMatch && fillMatch) {
            await page.getByRole(roleMatch[1] as any, { name: roleMatch[2] }).fill(fillMatch[1]);
          }
        }
      } else if (command.startsWith('getByText(')) {
        const text = command.match(/getByText\(['"](.+?)['"]\)/)?.[1];
        if (text && command.includes('.click()')) {
          await page.getByText(text).click();
        }
      } else if (command.startsWith('waitForLoadState(')) {
        await page.waitForLoadState('load');
      }
      // Add more safe commands as needed
    }
  }

  private extractSelector(input: string): string | null {
    // Extract selector from quotes
    const match = input.match(/['"](.+?)['"]/);
    return match ? match[1] : null;
  }

  async executeMultipleActions(
    actions: Array<{ code: string; description: string }>
  ): Promise<ExecutionResult> {
    const executedCodes: string[] = [];
    const results: string[] = [];

    for (const action of actions) {
      const result = await this.executeAction(action.code, action.description);
      executedCodes.push(result.executedCode);
      results.push(result.result);

      if (!result.success) {
        // Stop on first error
        return {
          success: false,
          result: results.join("\n"),
          executedCode: executedCodes.join("\n"),
          pageState: result.pageState,
          error: result.error,
        };
      }
    }

    return {
      success: true,
      result: results.join("\n"),
      executedCode: executedCodes.join("\n"),
      pageState: await this.getPageState(),
    };
  }

  private async getPageState(): Promise<string> {
    if (!this.page) {
      return "No page loaded";
    }

    try {
      const url = this.page.url();
      const title = await this.page.title();
      
      // Get simplified accessibility snapshot (similar to Playwright MCP)
      // This is a basic version - Playwright MCP has more advanced accessibility tree extraction
      const snapshot = await this.page.accessibility.snapshot();
      
      let accessibilityInfo = "Page elements:\n";
      if (snapshot) {
        accessibilityInfo += this.formatAccessibilityTree(snapshot, 0);
      }

      return `URL: ${url}\nTitle: ${title}\n\n${accessibilityInfo}`;
    } catch (error) {
      return `Error getting page state: ${error}`;
    }
  }

  private formatAccessibilityTree(node: any, depth: number): string {
    const indent = "  ".repeat(depth);
    let result = "";

    if (node.role && node.name) {
      result += `${indent}- ${node.role}: "${node.name}"\n`;
    }

    if (node.children) {
      for (const child of node.children.slice(0, 10)) { // Limit to first 10 for brevity
        result += this.formatAccessibilityTree(child, depth + 1);
      }
    }

    return result;
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.context = null;
      this.page = null;
    }
  }

  async getCurrentPageSnapshot(): Promise<string> {
    return this.getPageState();
  }
}

// Singleton instance for session persistence
export const playwrightExecutor = new PlaywrightExecutor();
