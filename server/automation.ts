import { Stagehand } from "@browserbasehq/stagehand";
import type { Page } from "playwright";
import { WebSocket } from "ws";

export type AutomationModel = "openai" | "anthropic" | "gemini";

// Note: In Stagehand v3, act/extract/observe are called on the Stagehand instance, not the Page

interface AutomationLog {
  timestamp: number;
  action: string;
  status: string;
  details?: any;
}

interface AutomationResult {
  success: boolean;
  result?: any;
  error?: string;
  logs: AutomationLog[];
  duration: string;
}

export class AutomationExecutor {
  private stagehand: Stagehand | null = null;
  private page: Page | null = null;
  private logs: AutomationLog[] = [];
  private ws: WebSocket | null = null;

  constructor(ws?: WebSocket) {
    this.ws = ws || null;
  }

  private log(action: string, status: string, details?: any) {
    const log = {
      timestamp: Date.now(),
      action,
      status,
      details,
    };
    this.logs.push(log);

    // Only send if WebSocket is connected
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({
          type: "execution_log",
          data: { log },
        }));
      } catch (error) {
        // Silently fail if WebSocket send fails (connection closed)
        console.error("Failed to send log over WebSocket:", error);
      }
    }
  }

  async initialize(model: AutomationModel): Promise<void> {
    this.log("Initializing browser automation", "running");

    try {
      // Stagehand v3 automatically picks up API keys from environment variables
      const apiKeys = {
        openai: process.env.OPENAI_API_KEY,
        anthropic: process.env.ANTHROPIC_API_KEY,
        gemini: process.env.GEMINI_API_KEY,
      };

      const apiKey = apiKeys[model];
      if (!apiKey) {
        throw new Error(`API key not found for model: ${model}. Please set ${model.toUpperCase()}_API_KEY environment variable.`);
      }

      this.stagehand = new Stagehand({
        env: "LOCAL",
        verbose: 1,
        model: model === "openai" ? "openai/gpt-4o-mini" : model === "anthropic" ? "anthropic/claude-3-5-sonnet-20241022" : "google/gemini-2.0-flash-exp",
      });

      await this.stagehand.init();
      
      // Get the page from context (official Stagehand v3 pattern)
      this.page = this.stagehand.context.pages()[0] as Page;

      this.log("Browser automation initialized", "success", { model });
    } catch (error: any) {
      this.log("Failed to initialize browser", "error", { error: error.message });
      throw error;
    }
  }

  async execute(prompt: string): Promise<AutomationResult> {
    const startTime = Date.now();

    try {
      if (!this.stagehand || !this.page) {
        throw new Error("Automation not initialized");
      }

      this.log(`Executing: ${prompt}`, "running");

      // Extract URL from prompt if present and navigate first (official pattern)
      const urlMatch = prompt.match(/(?:go to|open|navigate to|visit)\s+(?:https?:\/\/)?([^\s,]+\.[^\s,]+)/i);
      if (urlMatch) {
        const url = urlMatch[1].startsWith('http') ? urlMatch[1] : `https://${urlMatch[1]}`;
        this.log(`Navigating to ${url}`, "running");
        await this.page.goto(url, { waitUntil: 'domcontentloaded' });
        this.log("Navigation completed", "success");
      }

      // Use Stagehand's act method for actions (official v3 API)
      this.log("Processing automation with AI", "running");
      const result = await this.stagehand.act(prompt);

      this.log("Automation completed successfully", "success", { result });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: true,
        result,
        logs: this.logs,
        duration,
      };
    } catch (error: any) {
      this.log("Automation failed", "error", { error: error.message });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: false,
        error: error.message,
        logs: this.logs,
        duration,
      };
    }
  }

  async extract(prompt: string, instruction: string, schema?: any): Promise<AutomationResult> {
    const startTime = Date.now();

    try {
      if (!this.stagehand) {
        throw new Error("Automation not initialized");
      }

      this.log(`Navigating and extracting: ${instruction}`, "running");

      // First navigate or perform action if needed
      if (prompt) {
        await this.stagehand.act(prompt);
        this.log("Navigation completed", "success");
      }

      // Extract data (v3 API: extract is called on stagehand with instruction and schema)
      this.log("Extracting data", "running");
      const result = await this.stagehand.extract(instruction, schema || { data: "string" });

      this.log("Data extracted successfully", "success", { result });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: true,
        result,
        logs: this.logs,
        duration,
      };
    } catch (error: any) {
      this.log("Extraction failed", "error", { error: error.message });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: false,
        error: error.message,
        logs: this.logs,
        duration,
      };
    }
  }

  async observe(instruction: string): Promise<AutomationResult> {
    const startTime = Date.now();

    try {
      if (!this.stagehand) {
        throw new Error("Automation not initialized");
      }

      this.log(`Observing: ${instruction}`, "running");

      // v3 API: observe is called on stagehand with instruction
      const result = await this.stagehand.observe(instruction);

      this.log("Observation completed", "success", { result });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: true,
        result,
        logs: this.logs,
        duration,
      };
    } catch (error: any) {
      this.log("Observation failed", "error", { error: error.message });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: false,
        error: error.message,
        logs: this.logs,
        duration,
      };
    }
  }

  async cleanup(): Promise<void> {
    try {
      if (this.stagehand) {
        await this.stagehand.close();
        this.log("Browser closed", "success");
      }
    } catch (error: any) {
      this.log("Cleanup failed", "error", { error: error.message });
    }
  }

  getLogs(): AutomationLog[] {
    return this.logs;
  }
}
