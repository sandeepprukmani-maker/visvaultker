import { Stagehand, AISdkClient } from "@browserbasehq/stagehand";
import { createOpenAI } from "@ai-sdk/openai";
import { spawn } from "child_process";
import { storage } from "./storage";

/**
 * Fetch OAuth token by invoking Python script
 */
async function getOAuthToken(): Promise<string> {
  return new Promise((resolve, reject) => {
    // Use "python3" if needed. On Replit "python3" is standard.
    const pythonProcess = spawn("python3", ["fetch_token.py"]);

    let output = "";

    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error("Python stderr:", data.toString());
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        return reject(new Error("Python script failed"));
      }

      try {
        const result = JSON.parse(output.trim());
        resolve(result.access_token);
      } catch (err) {
        reject(
          new Error(`Failed to parse token from Python output: ${output}`)
        );
      }
    });
  });
}

// Helper to run automation in background
export async function runAutomation(automationId: number, prompt: string) {
  try {
    await storage.addLog({
      automationId,
      message: "Initializing Stagehand with custom provider...",
      type: "info",
    });

    // 1. Get OAuth Token
    let token = "dummy-token";
    try {
      token = await getOAuthToken();
    } catch (e) {
      console.warn("Failed to fetch OAuth token, using dummy. Ensure fetch_token.py is configured.");
    }

    // 2. Configure Custom OpenAI-compatible Provider
    const customProvider = createOpenAI({
      baseURL: "https://perf-apigw-int.saifg.rbc.com/JLCO/llm-control-stack/v1",
      apiKey: "unused",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const stagehand = new Stagehand({
      env: "LOCAL",
      verbose: 2,
      headless: true,
      executablePath: process.env.CHROME_PATH,
      enableProxy: false,
      llmClient: new AISdkClient({
        model: customProvider.chat(
          "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        ),
      }),
    } as any);

    await stagehand.init();
    
    await storage.addLog({
      automationId,
      message: "Browser initialized with custom model. Starting action...",
      type: "info",
    });

    try {
        await storage.addLog({
            automationId,
            message: `Executing: ${prompt}`,
            type: "action",
        });

        const result = await stagehand.act(prompt);
        
        const pages = stagehand.context.pages();
        const page = pages.length > 0 ? pages[0] : await stagehand.context.newPage();
        let screenshot: string | undefined;
        
        if (page) {
             const buffer = await page.screenshot();
             screenshot = buffer.toString('base64');
        }

        await storage.updateAutomation(automationId, {
            status: "completed",
            result: { message: "Action completed successfully", output: result },
            screenshot: screenshot ? `data:image/png;base64,${screenshot}` : undefined
        });

        await storage.addLog({
            automationId,
            message: "Automation completed successfully.",
            type: "info",
        });

    } catch (actionError: any) {
        throw actionError;
    } finally {
        await stagehand.close();
    }

  } catch (error: any) {
    console.error("Automation error:", error);
    await storage.updateAutomation(automationId, {
      status: "failed",
      error: error.message || "Unknown error occurred",
    });
    
    await storage.addLog({
      automationId,
      message: `Error: ${error.message}`,
      type: "error",
    });
  }
}
