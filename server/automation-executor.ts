import { storage } from "./storage";
import { callMcpTool, getMcpClient } from "./mcp-client";
import { planBrowserActions, summarizeResult } from "./openai-service";
import type { AutomationTask, BrowserAction } from "@shared/schema";
import type { WebSocket } from "ws";

type WSBroadcast = (message: object) => void;

export async function executeAutomation(
  taskId: string,
  prompt: string,
  broadcast: WSBroadcast
): Promise<AutomationTask> {
  let task = await storage.updateTask(taskId, { status: "running" });
  if (!task) {
    throw new Error("Task not found");
  }

  broadcast({ type: "task_update", task });

  try {
    const client = await getMcpClient();
    if (!client) {
      throw new Error("Browser not connected. Please wait for the connection to establish.");
    }

    const plan = await planBrowserActions(prompt);
    console.log("Action plan:", JSON.stringify(plan, null, 2));

    const executedActions: { tool: string; result: unknown; error?: string }[] = [];

    for (const plannedAction of plan.actions) {
      const action = await storage.addAction(taskId, {
        type: plannedAction.tool,
        target: plannedAction.description,
        value: JSON.stringify(plannedAction.args),
        status: "running",
        timestamp: Date.now(),
      });

      task = await storage.getTask(taskId);
      if (task) {
        broadcast({ type: "task_update", task });
      }

      try {
        console.log(`Executing: ${plannedAction.tool}`, plannedAction.args);
        const result = await callMcpTool(plannedAction.tool, plannedAction.args);
        
        if (action) {
          await storage.updateAction(taskId, action.id, {
            status: "success",
            result: typeof result === "string" ? result : JSON.stringify(result),
          });
        }

        executedActions.push({
          tool: plannedAction.tool,
          result,
        });

        task = await storage.getTask(taskId);
        if (task) {
          broadcast({ type: "task_update", task });
        }

        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        
        if (action) {
          await storage.updateAction(taskId, action.id, {
            status: "error",
            error: errorMessage,
          });
        }

        executedActions.push({
          tool: plannedAction.tool,
          result: null,
          error: errorMessage,
        });

        task = await storage.getTask(taskId);
        if (task) {
          broadcast({ type: "task_update", task });
        }
      }
    }

    const hasErrors = executedActions.some((a) => a.error);
    const resultSummary = await summarizeResult(prompt, executedActions);

    task = await storage.updateTask(taskId, {
      status: hasErrors ? "error" : "success",
      result: resultSummary,
      completedAt: Date.now(),
    });

    if (task) {
      broadcast({ type: "task_update", task });
    }

    return task!;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    
    task = await storage.updateTask(taskId, {
      status: "error",
      error: errorMessage,
      completedAt: Date.now(),
    });

    if (task) {
      broadcast({ type: "task_update", task });
    }

    throw error;
  }
}
