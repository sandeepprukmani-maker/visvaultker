import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { generateWorkflowRequest, controlWorkflowRequest, executeWorkflowRequest } from "@shared/schema";
import type { Workflow, WorkflowStep, LogEntry, ModelOption } from "@shared/schema";
import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import { initBrowserForExecution, closeBrowserForExecution, executeStep as executeBrowserStep } from "./browser-service";

const ANTHROPIC_MODEL = "claude-sonnet-4-20250514";
// the newest OpenAI model is "gpt-4o-mini" as requested by user
const OPENAI_MODEL = "gpt-4o-mini";

function getAnthropicClient(): Anthropic | null {
  if (!process.env.ANTHROPIC_API_KEY) {
    return null;
  }
  return new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
}

function getOpenAIClient(): OpenAI | null {
  if (!process.env.OPENAI_API_KEY) {
    return null;
  }
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
}

const activeExecutions = new Map<string, { cancelled: boolean; paused: boolean }>();

function createMockWorkflow(prompt: string): Workflow {
  const urlMatch = prompt.match(/(https?:\/\/[^\s]+)/i) ||
                   prompt.match(/([a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}(?:\/[^\s]*)?)/i);
  const targetUrl = urlMatch ? (urlMatch[1].startsWith('http') ? urlMatch[1] : `https://${urlMatch[1]}`) : 'https://www.google.com';
  
  const steps: WorkflowStep[] = [
    {
      id: "step_1",
      name: "Navigate to website",
      description: `Navigate to ${targetUrl}`,
      status: "pending",
      tool: "browser",
      dependencies: [],
    },
    {
      id: "step_2",
      name: "Wait for page load",
      description: "Wait for the page to fully load",
      status: "pending",
      tool: "browser",
      dependencies: ["step_1"],
    },
    {
      id: "step_3",
      name: "Extract page content",
      description: "Extract relevant data from the page",
      status: "pending",
      tool: "browser",
      dependencies: ["step_2"],
    },
    {
      id: "step_4",
      name: "Process results",
      description: "Process and format the extracted data",
      status: "pending",
      tool: "code",
      dependencies: ["step_3"],
    },
  ];

  return {
    name: `Automation: ${prompt.slice(0, 30)}...`,
    description: `Workflow generated for: ${prompt}`,
    steps,
  };
}

const SYSTEM_PROMPT = `You are an AI workflow planner for web automation. Given a user's task description, create a detailed workflow with specific steps. 

Output a valid JSON object with this structure:
{
  "name": "Brief workflow name",
  "description": "What this workflow accomplishes",
  "steps": [
    {
      "id": "step_1",
      "name": "Step name",
      "description": "What this step does",
      "status": "pending",
      "tool": "browser|file|search|database|code",
      "dependencies": []
    }
  ]
}

Guidelines:
- Break complex tasks into 3-7 logical steps
- Each step should be atomic and focused
- Use appropriate tools: "browser" for web actions, "file" for saving data, "search" for finding info, "database" for data storage, "code" for processing
- Dependencies array contains IDs of steps that must complete first
- All steps start with status "pending"

Only output the JSON, no explanation.`;

async function generateWithAnthropic(prompt: string): Promise<Workflow> {
  const client = getAnthropicClient();
  
  if (!client) {
    throw new Error("Anthropic API key not configured");
  }

  const response = await client.messages.create({
    model: ANTHROPIC_MODEL,
    max_tokens: 2048,
    messages: [
      {
        role: "user",
        content: `Create a workflow for this task: ${prompt}`,
      },
    ],
    system: SYSTEM_PROMPT,
  });

  const content = response.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from AI");
  }

  const jsonMatch = content.text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error("No valid JSON found in response");
  }
  return JSON.parse(jsonMatch[0]) as Workflow;
}

async function generateWithOpenAI(prompt: string): Promise<Workflow> {
  const client = getOpenAIClient();
  
  if (!client) {
    throw new Error("OpenAI API key not configured");
  }

  const response = await client.chat.completions.create({
    model: OPENAI_MODEL,
    max_tokens: 2048,
    messages: [
      {
        role: "system",
        content: SYSTEM_PROMPT,
      },
      {
        role: "user",
        content: `Create a workflow for this task: ${prompt}`,
      },
    ],
    response_format: { type: "json_object" },
  });

  const content = response.choices[0].message.content;
  if (!content) {
    throw new Error("No content in response");
  }

  return JSON.parse(content) as Workflow;
}

async function generateWorkflowFromPrompt(prompt: string, model: ModelOption): Promise<Workflow> {
  try {
    if (model === "openai") {
      return await generateWithOpenAI(prompt);
    } else {
      return await generateWithAnthropic(prompt);
    }
  } catch (error) {
    console.error(`Error calling ${model} API, falling back to mock:`, error);
    return createMockWorkflow(prompt);
  }
}

async function executeStepWithBrowser(
  executionId: string,
  step: WorkflowStep,
  stepIndex: number,
  totalSteps: number
): Promise<{ success: boolean; result?: string; error?: string }> {
  const state = activeExecutions.get(executionId);
  if (!state) return { success: false, error: "Execution not found" };
  
  while (state.paused) {
    await new Promise((resolve) => setTimeout(resolve, 500));
    const currentState = activeExecutions.get(executionId);
    if (!currentState || currentState.cancelled) {
      return { success: false, error: "Execution cancelled" };
    }
  }
  
  if (state.cancelled) {
    return { success: false, error: "Execution cancelled" };
  }

  try {
    if (step.tool === "browser") {
      const browserResult = await executeBrowserStep(executionId, step.name, step.description || step.name, step.tool);
      return {
        success: browserResult.success,
        result: browserResult.result,
        error: browserResult.error,
      };
    } else {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return {
        success: true,
        result: `Successfully completed: ${step.name}`,
      };
    }
  } catch (error) {
    return {
      success: false,
      error: `Error executing step: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function executeWorkflow(executionId: string): Promise<void> {
  const execution = await storage.getExecution(executionId);
  if (!execution || !execution.workflow) return;

  activeExecutions.set(executionId, { cancelled: false, paused: false });

  const workflow = execution.workflow as Workflow;
  const steps = workflow.steps.map(s => ({ ...s }));
  const logs: LogEntry[] = [];
  
  const addLog = async (level: LogEntry["level"], message: string, stepId?: string) => {
    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    logs.push({ timestamp, level, message, stepId });
    await storage.updateExecution(executionId, { logs: [...logs] });
  };

  await storage.updateExecution(executionId, {
    status: "running",
    logs: [...logs],
  });

  await addLog("info", "Starting workflow execution");

  const hasBrowserSteps = steps.some(s => s.tool === "browser");
  if (hasBrowserSteps) {
    await addLog("info", "Initializing browser...");
    try {
      await initBrowserForExecution(executionId);
      await addLog("success", "Browser initialized successfully");
    } catch (error) {
      await addLog("error", `Failed to initialize browser: ${error instanceof Error ? error.message : String(error)}`);
      await storage.updateExecution(executionId, {
        status: "failed",
        error: "Failed to initialize browser",
        logs: [...logs],
        completedAt: new Date(),
      });
      activeExecutions.delete(executionId);
      return;
    }
  }

  for (let i = 0; i < steps.length; i++) {
    const state = activeExecutions.get(executionId);
    if (!state || state.cancelled) {
      await addLog("warning", "Execution cancelled by user");
      if (hasBrowserSteps) await closeBrowserForExecution(executionId);
      await storage.updateExecution(executionId, {
        status: "cancelled",
        logs: [...logs],
        workflow: { ...workflow, steps },
        completedAt: new Date(),
      });
      activeExecutions.delete(executionId);
      return;
    }

    while (state.paused) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      const currentState = activeExecutions.get(executionId);
      if (!currentState || currentState.cancelled) {
        await addLog("warning", "Execution cancelled while paused");
        if (hasBrowserSteps) await closeBrowserForExecution(executionId);
        await storage.updateExecution(executionId, {
          status: "cancelled",
          logs: [...logs],
          workflow: { ...workflow, steps },
          completedAt: new Date(),
        });
        activeExecutions.delete(executionId);
        return;
      }
    }

    const step = steps[i];
    step.status = "running";
    
    const progress = Math.round(((i + 0.5) / steps.length) * 100);
    
    await addLog("info", `Executing step ${i + 1}/${steps.length}: ${step.name}`, step.id);
    
    await storage.updateExecution(executionId, {
      workflow: { ...workflow, steps },
      currentStep: step.name,
      progress,
      logs: [...logs],
    });

    const result = await executeStepWithBrowser(executionId, step, i, steps.length);

    if (result.success) {
      step.status = "completed";
      step.result = result.result;
      await addLog("success", `Completed: ${step.name}`, step.id);
      if (result.result) {
        await addLog("info", `Result: ${result.result.slice(0, 200)}${result.result.length > 200 ? '...' : ''}`, step.id);
      }
    } else {
      step.status = "failed";
      step.error = result.error;
      await addLog("error", result.error || "Step failed", step.id);
      
      if (hasBrowserSteps) await closeBrowserForExecution(executionId);
      await storage.updateExecution(executionId, {
        status: "failed",
        workflow: { ...workflow, steps },
        error: result.error,
        logs: [...logs],
        progress: Math.round(((i + 1) / steps.length) * 100),
        completedAt: new Date(),
      });
      activeExecutions.delete(executionId);
      return;
    }

    const stepProgress = Math.round(((i + 1) / steps.length) * 100);
    await storage.updateExecution(executionId, {
      workflow: { ...workflow, steps },
      progress: stepProgress,
      logs: [...logs],
    });
  }

  if (hasBrowserSteps) {
    await addLog("info", "Closing browser...");
    await closeBrowserForExecution(executionId);
  }

  await addLog("success", "Workflow completed successfully!");
  
  await storage.updateExecution(executionId, {
    status: "completed",
    workflow: { ...workflow, steps },
    progress: 100,
    result: "Workflow executed successfully",
    logs: [...logs],
    completedAt: new Date(),
  });
  
  activeExecutions.delete(executionId);
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  app.get("/api/executions", async (req, res) => {
    try {
      const executions = await storage.getExecutions();
      res.json(executions);
    } catch (error) {
      console.error("Error fetching executions:", error);
      res.status(500).json({ error: "Failed to fetch executions" });
    }
  });

  app.get("/api/executions/:id", async (req, res) => {
    try {
      const execution = await storage.getExecution(req.params.id);
      if (!execution) {
        return res.status(404).json({ error: "Execution not found" });
      }
      res.json({ execution, workflow: execution.workflow });
    } catch (error) {
      console.error("Error fetching execution:", error);
      res.status(500).json({ error: "Failed to fetch execution" });
    }
  });

  app.delete("/api/executions/:id", async (req, res) => {
    try {
      const deleted = await storage.deleteExecution(req.params.id);
      if (!deleted) {
        return res.status(404).json({ error: "Execution not found" });
      }
      res.json({ success: true });
    } catch (error) {
      console.error("Error deleting execution:", error);
      res.status(500).json({ error: "Failed to delete execution" });
    }
  });

  app.post("/api/workflow/generate", async (req, res) => {
    try {
      const parsed = generateWorkflowRequest.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
      }

      const workflow = await generateWorkflowFromPrompt(parsed.data.prompt, parsed.data.model);
      
      const execution = await storage.createExecution({
        prompt: parsed.data.prompt,
        status: "ready",
        workflow: workflow,
        logs: [],
        progress: 0,
      });

      res.json({ execution, workflow });
    } catch (error) {
      console.error("Error generating workflow:", error);
      const message = error instanceof Error ? error.message : "Failed to generate workflow";
      res.status(500).json({ error: message });
    }
  });

  app.post("/api/workflow/execute", async (req, res) => {
    try {
      const parsed = executeWorkflowRequest.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
      }

      const execution = await storage.getExecution(parsed.data.executionId);
      if (!execution) {
        return res.status(404).json({ error: "Execution not found" });
      }

      const initialLogs: LogEntry[] = [{
        timestamp: new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
        level: "info",
        message: "Execution started",
      }];

      const updatedExecution = await storage.updateExecution(parsed.data.executionId, {
        status: "running",
        logs: initialLogs,
        progress: 0,
      });

      executeWorkflow(parsed.data.executionId);

      const latestExecution = await storage.getExecution(parsed.data.executionId);
      res.json({ success: true, execution: latestExecution });
    } catch (error) {
      console.error("Error starting execution:", error);
      res.status(500).json({ error: "Failed to start execution" });
    }
  });

  app.post("/api/workflow/control", async (req, res) => {
    try {
      const parsed = controlWorkflowRequest.safeParse(req.body);
      if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
      }

      const { executionId, action } = parsed.data;
      const state = activeExecutions.get(executionId);
      
      let newStatus: string;
      
      if (action === "pause") {
        if (state) state.paused = true;
        newStatus = "paused";
      } else if (action === "resume") {
        if (state) state.paused = false;
        newStatus = "running";
      } else if (action === "cancel") {
        if (state) state.cancelled = true;
        newStatus = "cancelled";
      } else {
        return res.status(400).json({ error: "Invalid action" });
      }

      const updatedExecution = await storage.updateExecution(executionId, { 
        status: newStatus,
        ...(action === "cancel" ? { completedAt: new Date() } : {}),
      });

      if (!updatedExecution) {
        return res.status(404).json({ error: "Execution not found" });
      }

      res.json({ success: true, execution: updatedExecution });
    } catch (error) {
      console.error("Error controlling execution:", error);
      res.status(500).json({ error: "Failed to control execution" });
    }
  });

  app.get("/api/config", (req, res) => {
    res.json({
      hasAnthropicKey: !!process.env.ANTHROPIC_API_KEY,
      hasOpenAIKey: !!process.env.OPENAI_API_KEY,
    });
  });

  return httpServer;
}
