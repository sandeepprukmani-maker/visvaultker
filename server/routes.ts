import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { generateWorkflowRequest, controlWorkflowRequest, executeWorkflowRequest } from "@shared/schema";
import type { Workflow, WorkflowStep, LogEntry } from "@shared/schema";
import Anthropic from "@anthropic-ai/sdk";

const DEFAULT_MODEL = "claude-sonnet-4-20250514";

function getAnthropicClient(): Anthropic | null {
  if (!process.env.ANTHROPIC_API_KEY) {
    return null;
  }
  return new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
}

const activeExecutions = new Map<string, { cancelled: boolean; paused: boolean }>();

function createMockWorkflow(prompt: string): Workflow {
  const steps: WorkflowStep[] = [
    {
      id: "step_1",
      name: "Initialize browser session",
      description: "Start a new browser instance for automation",
      status: "pending",
      tool: "browser",
      dependencies: [],
    },
    {
      id: "step_2",
      name: "Navigate to target",
      description: `Navigate to the target URL based on: ${prompt.slice(0, 50)}...`,
      status: "pending",
      tool: "browser",
      dependencies: ["step_1"],
    },
    {
      id: "step_3",
      name: "Extract data",
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
    {
      id: "step_5",
      name: "Save output",
      description: "Save the processed data to a file",
      status: "pending",
      tool: "file",
      dependencies: ["step_4"],
    },
  ];

  return {
    name: `Automation: ${prompt.slice(0, 30)}...`,
    description: `Workflow generated for: ${prompt}`,
    steps,
  };
}

async function generateWorkflowFromPrompt(prompt: string): Promise<Workflow> {
  const client = getAnthropicClient();
  
  if (!client) {
    console.log("No Anthropic API key configured, using mock workflow");
    return createMockWorkflow(prompt);
  }
  
  const systemPrompt = `You are an AI workflow planner for web automation. Given a user's task description, create a detailed workflow with specific steps. 

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

  try {
    const response = await client.messages.create({
      model: DEFAULT_MODEL,
      max_tokens: 2048,
      messages: [
        {
          role: "user",
          content: `Create a workflow for this task: ${prompt}`,
        },
      ],
      system: systemPrompt,
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
  } catch (error) {
    console.error("Error calling Anthropic API, falling back to mock:", error);
    return createMockWorkflow(prompt);
  }
}

async function simulateStepExecution(
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

  const baseTime = 1500;
  const variance = Math.random() * 1000;
  await new Promise((resolve) => setTimeout(resolve, baseTime + variance));

  const successRate = 0.95;
  const success = Math.random() < successRate;

  if (success) {
    const results = [
      `Successfully completed: ${step.name}`,
      `Data extracted from target`,
      `Action performed successfully`,
      `Information gathered and processed`,
      `Step completed with expected results`,
    ];
    return {
      success: true,
      result: results[Math.floor(Math.random() * results.length)],
    };
  } else {
    return {
      success: false,
      error: `Failed to complete step: ${step.name}`,
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

  for (let i = 0; i < steps.length; i++) {
    const state = activeExecutions.get(executionId);
    if (!state || state.cancelled) {
      await addLog("warning", "Execution cancelled by user");
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

    const result = await simulateStepExecution(executionId, step, i, steps.length);

    if (result.success) {
      step.status = "completed";
      step.result = result.result;
      await addLog("success", `Completed: ${step.name}`, step.id);
    } else {
      step.status = "failed";
      step.error = result.error;
      await addLog("error", result.error || "Step failed", step.id);
      
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

      const workflow = await generateWorkflowFromPrompt(parsed.data.prompt);
      
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
    });
  });

  return httpServer;
}
