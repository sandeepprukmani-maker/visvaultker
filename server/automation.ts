import { Stagehand } from "@browserbasehq/stagehand";
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
  private page: any = null;
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
        cacheDir: "stagehand-cache",
        model: model === "openai" ? "openai/gpt-4o-mini" : model === "anthropic" ? "anthropic/claude-3-5-sonnet-20241022" : "google/gemini-2.0-flash-exp",
      });

      await this.stagehand.init();
      
      // Get the page from context (official Stagehand v3 pattern)
      this.page = this.stagehand.context.pages()[0];

      this.log("Browser automation initialized with caching enabled", "success", { model });
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

      // Parse multi-step instructions by splitting on common action keywords
      const steps = this.parseMultiStepPrompt(prompt);
      
      if (steps.length > 1) {
        this.log(`Detected ${steps.length} steps to execute`, "running");
        
        const results = [];
        for (let i = 0; i < steps.length; i++) {
          const step = steps[i];
          this.log(`Step ${i + 1}/${steps.length}: ${step}`, "running");
          
          const stepResult = await this.stagehand.act(step);
          results.push(stepResult);
          
          this.log(`Step ${i + 1} completed`, "success", { result: stepResult });
          
          // Add a small delay between steps to allow page updates
          if (i < steps.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
        
        this.log("All steps completed successfully", "success");
        
        const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;
        
        return {
          success: true,
          result: results[results.length - 1],
          logs: this.logs,
          duration,
        };
      } else {
        // Single step execution
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
      }
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

  async executeAgent(prompt: string, model: AutomationModel): Promise<AutomationResult> {
    const startTime = Date.now();

    try {
      if (!this.stagehand || !this.page) {
        throw new Error("Automation not initialized");
      }

      this.log(`Executing with Agent mode: ${prompt}`, "running");

      // Extract URL from prompt if present and navigate first
      const urlMatch = prompt.match(/(?:go to|open|navigate to|visit)\s+(?:https?:\/\/)?([^\s,]+\.[^\s,]+)/i);
      if (urlMatch) {
        const url = urlMatch[1].startsWith('http') ? urlMatch[1] : `https://${urlMatch[1]}`;
        this.log(`Navigating to ${url}`, "running");
        await this.page.goto(url, { waitUntil: 'domcontentloaded' });
        this.log("Navigation completed", "success");
      }

      // Map model to agent model names (using standard models, not CUA for now)
      const agentModel = model === "openai" 
        ? "openai/gpt-4o-mini" 
        : model === "anthropic" 
        ? "anthropic/claude-3-5-sonnet-20241022" 
        : "google/gemini-2.0-flash-exp";

      this.log("Creating autonomous agent", "running");
      
      // Create agent with the selected model
      const agent = this.stagehand.agent({
        model: agentModel,
        systemPrompt: "You are a helpful assistant that can control a web browser to automate tasks. Complete all steps in the user's instruction."
      });

      this.log("Agent executing workflow", "running");
      
      // Execute the entire workflow with the agent
      const result = await agent.execute(prompt);

      this.log("Agent workflow completed successfully", "success", { result });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: true,
        result,
        logs: this.logs,
        duration,
      };
    } catch (error: any) {
      this.log("Agent execution failed", "error", { error: error.message });

      const duration = `${((Date.now() - startTime) / 1000).toFixed(1)}s`;

      return {
        success: false,
        error: error.message,
        logs: this.logs,
        duration,
      };
    }
  }

  private parseMultiStepPrompt(prompt: string): string[] {
    // Remove the navigation part if present (already handled separately)
    let cleanPrompt = prompt.replace(/(?:go to|open|navigate to|visit)\s+(?:https?:\/\/)?([^\s,]+\.[^\s,]+)\s*/i, '');
    
    if (!cleanPrompt.trim()) {
      return [];
    }
    
    // Split on action keywords while preserving the action in each step
    const actionKeywords = [
      'click on', 'click', 'press', 'tap',
      'type', 'enter', 'fill', 'input',
      'select', 'choose',
      'scroll to', 'scroll',
      'hover over', 'hover',
      'wait for',
      'submit',
      'upload'
    ];
    
    // Create regex pattern to split on action keywords
    const pattern = new RegExp(`\\b(${actionKeywords.join('|')})\\s`, 'gi');
    
    // Split the prompt, keeping the delimiters
    const parts: string[] = [];
    let lastIndex = 0;
    let match;
    
    while ((match = pattern.exec(cleanPrompt)) !== null) {
      if (match.index > lastIndex) {
        const prevText = cleanPrompt.slice(lastIndex, match.index).trim();
        if (prevText && parts.length > 0) {
          parts[parts.length - 1] += ' ' + prevText;
        }
      }
      
      const restOfPrompt = cleanPrompt.slice(match.index);
      const nextMatch = pattern.exec(cleanPrompt);
      
      if (nextMatch) {
        pattern.lastIndex = match.index + 1;
        parts.push(restOfPrompt.slice(0, nextMatch.index - match.index).trim());
      } else {
        parts.push(restOfPrompt.trim());
        break;
      }
      
      lastIndex = match.index;
    }
    
    if (parts.length === 0 && cleanPrompt.trim()) {
      parts.push(cleanPrompt.trim());
    }
    
    return parts.filter(p => p.length > 0);
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
