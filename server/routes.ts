import type { Express, RequestHandler } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { 
  insertTaskSchema, 
  insertExecutionSchema, 
  insertRecordingSchema, 
  insertWorkflowSchema,
  updateTaskSchema,
  updateExecutionSchema,
  updateRecordingSchema,
  updateWorkflowSchema
} from "@shared/schema";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const devAuthBypass: RequestHandler = (req: any, res, next) => {
  if (!req.user) {
    req.user = { claims: { sub: 'dev-user-1' } };
  }
  next();
};

const authMiddleware = process.env.NODE_ENV === 'production' ? isAuthenticated : devAuthBypass;

export async function registerRoutes(app: Express): Promise<Server> {
  // Set up auth middleware and routes
  await setupAuth(app);

  // Auth user endpoint
  app.get('/api/auth/user', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // Task routes
  app.get('/api/tasks', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const tasks = await storage.getTasks(userId);
      res.json(tasks);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      res.status(500).json({ message: "Failed to fetch tasks" });
    }
  });

  app.post('/api/tasks', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertTaskSchema.safeParse({ ...req.body, userId });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid task data", errors: validation.error.errors });
      }
      const task = await storage.createTask(validation.data);
      res.json(task);
    } catch (error) {
      console.error("Error creating task:", error);
      res.status(500).json({ message: "Failed to create task" });
    }
  });

  app.get('/api/tasks/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const task = await storage.getTask(req.params.id, userId);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.json(task);
    } catch (error) {
      console.error("Error fetching task:", error);
      res.status(500).json({ message: "Failed to fetch task" });
    }
  });

  app.patch('/api/tasks/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = updateTaskSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid task data", errors: validation.error.errors });
      }
      const task = await storage.updateTask(req.params.id, userId, validation.data);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.json(task);
    } catch (error) {
      console.error("Error updating task:", error);
      res.status(500).json({ message: "Failed to update task" });
    }
  });

  app.delete('/api/tasks/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const deleted = await storage.deleteTask(req.params.id, userId);
      if (!deleted) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.json({ success: true });
    } catch (error) {
      console.error("Error deleting task:", error);
      res.status(500).json({ message: "Failed to delete task" });
    }
  });

  // Execution routes
  app.get('/api/tasks/:taskId/executions', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const executions = await storage.getExecutions(req.params.taskId, userId);
      res.json(executions);
    } catch (error) {
      console.error("Error fetching executions:", error);
      res.status(500).json({ message: "Failed to fetch executions" });
    }
  });

  app.post('/api/tasks/:taskId/execute', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const task = await storage.getTask(req.params.taskId, userId);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      
      const validation = insertExecutionSchema.safeParse({
        taskId: req.params.taskId,
        userId,
        status: "running",
      });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid execution data", errors: validation.error.errors });
      }
      
      const execution = await storage.createExecution(validation.data);
      
      const startTime = Date.now();
      try {
        const { stdout, stderr } = await execAsync(task.code, {
          timeout: 30000,
          maxBuffer: 1024 * 1024,
        });
        
        const duration = Date.now() - startTime;
        const logs = stdout + (stderr ? `\n--- STDERR ---\n${stderr}` : '');
        
        await storage.updateExecution(execution.id, userId, {
          status: "completed",
          finishedAt: new Date(),
          duration,
          logs,
          screenshotUrls: [],
        });
        
        const updatedExecution = await storage.getExecution(execution.id, userId);
        res.json(updatedExecution);
      } catch (execError: any) {
        const duration = Date.now() - startTime;
        await storage.updateExecution(execution.id, userId, {
          status: "failed",
          finishedAt: new Date(),
          duration,
          error: execError.message,
          logs: execError.stdout || '',
        });
        
        const updatedExecution = await storage.getExecution(execution.id, userId);
        res.json(updatedExecution);
      }
    } catch (error) {
      console.error("Error executing task:", error);
      res.status(500).json({ message: "Failed to execute task" });
    }
  });

  app.patch('/api/executions/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = updateExecutionSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid execution data", errors: validation.error.errors });
      }
      const execution = await storage.updateExecution(req.params.id, userId, validation.data);
      if (!execution) {
        return res.status(404).json({ message: "Execution not found" });
      }
      res.json(execution);
    } catch (error) {
      console.error("Error updating execution:", error);
      res.status(500).json({ message: "Failed to update execution" });
    }
  });

  app.get('/api/executions', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const tasks = await storage.getTasks(userId);
      const allExecutions = [];
      
      for (const task of tasks) {
        const executions = await storage.getExecutions(task.id, userId);
        allExecutions.push(...executions);
      }
      
      allExecutions.sort((a, b) => 
        new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
      );
      
      res.json(allExecutions);
    } catch (error) {
      console.error("Error fetching all executions:", error);
      res.status(500).json({ message: "Failed to fetch executions" });
    }
  });

  // Recording routes
  app.get('/api/recordings', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const recordings = await storage.getRecordings(userId);
      res.json(recordings);
    } catch (error) {
      console.error("Error fetching recordings:", error);
      res.status(500).json({ message: "Failed to fetch recordings" });
    }
  });

  app.post('/api/recordings', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertRecordingSchema.safeParse({ ...req.body, userId });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid recording data", errors: validation.error.errors });
      }
      const recording = await storage.createRecording(validation.data);
      res.json(recording);
    } catch (error) {
      console.error("Error creating recording:", error);
      res.status(500).json({ message: "Failed to create recording" });
    }
  });

  app.patch('/api/recordings/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = updateRecordingSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid recording data", errors: validation.error.errors });
      }
      const recording = await storage.updateRecording(req.params.id, userId, validation.data);
      if (!recording) {
        return res.status(404).json({ message: "Recording not found" });
      }
      res.json(recording);
    } catch (error) {
      console.error("Error updating recording:", error);
      res.status(500).json({ message: "Failed to update recording" });
    }
  });

  app.post('/api/recordings/:id/generate-code', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const recording = await storage.getRecording(req.params.id, userId);
      if (!recording) {
        return res.status(404).json({ message: "Recording not found" });
      }
      
      const actions = recording.actions as any[];
      let code = `import { test, expect } from '@playwright/test';\n\n`;
      code += `test('${recording.name}', async ({ page }) => {\n`;
      
      actions.forEach((action, index) => {
        if (action.type === 'navigate' && action.url) {
          code += `  // Step ${index + 1}: Navigate to ${action.url}\n`;
          code += `  await page.goto('${action.url}');\n\n`;
        } else if (action.type === 'click' && action.selector) {
          code += `  // Step ${index + 1}: Click on ${action.selector}\n`;
          code += `  await page.click('${action.selector}');\n\n`;
        } else if (action.type === 'input' && action.selector && action.value) {
          code += `  // Step ${index + 1}: Type into ${action.selector}\n`;
          code += `  await page.fill('${action.selector}', '${action.value}');\n\n`;
        } else if (action.type === 'keypress' && action.key) {
          code += `  // Step ${index + 1}: Press ${action.key}\n`;
          code += `  await page.keyboard.press('${action.key}');\n\n`;
        }
      });
      
      code += `});\n`;
      
      const updated = await storage.updateRecording(req.params.id, userId, {
        generatedCode: code,
        status: "completed",
      });
      
      res.json(updated);
    } catch (error) {
      console.error("Error generating code from recording:", error);
      res.status(500).json({ message: "Failed to generate code" });
    }
  });

  app.post('/api/recordings/:id/save-as-task', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const recording = await storage.getRecording(req.params.id, userId);
      if (!recording) {
        return res.status(404).json({ message: "Recording not found" });
      }
      
      if (!recording.generatedCode) {
        return res.status(400).json({ message: "Recording has no generated code. Generate code first." });
      }
      
      const task = await storage.createTask({
        userId,
        name: `${recording.name} (from recording)`,
        description: `Auto-generated task from recording: ${recording.name}`,
        code: recording.generatedCode,
        language: recording.language || "typescript",
        prompt: `Recording: ${recording.name}`,
      });
      
      res.json(task);
    } catch (error) {
      console.error("Error saving recording as task:", error);
      res.status(500).json({ message: "Failed to save recording as task" });
    }
  });

  app.delete('/api/recordings/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const deleted = await storage.deleteRecording(req.params.id, userId);
      if (!deleted) {
        return res.status(404).json({ message: "Recording not found" });
      }
      res.json({ success: true });
    } catch (error) {
      console.error("Error deleting recording:", error);
      res.status(500).json({ message: "Failed to delete recording" });
    }
  });

  // Workflow routes
  app.get('/api/workflows', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const workflows = await storage.getWorkflows(userId);
      res.json(workflows);
    } catch (error) {
      console.error("Error fetching workflows:", error);
      res.status(500).json({ message: "Failed to fetch workflows" });
    }
  });

  app.post('/api/workflows', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertWorkflowSchema.safeParse({ ...req.body, userId });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid workflow data", errors: validation.error.errors });
      }
      const workflow = await storage.createWorkflow(validation.data);
      res.json(workflow);
    } catch (error) {
      console.error("Error creating workflow:", error);
      res.status(500).json({ message: "Failed to create workflow" });
    }
  });

  app.patch('/api/workflows/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = updateWorkflowSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid workflow data", errors: validation.error.errors });
      }
      const workflow = await storage.updateWorkflow(req.params.id, userId, validation.data);
      if (!workflow) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.json(workflow);
    } catch (error) {
      console.error("Error updating workflow:", error);
      res.status(500).json({ message: "Failed to update workflow" });
    }
  });

  app.delete('/api/workflows/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const deleted = await storage.deleteWorkflow(req.params.id, userId);
      if (!deleted) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.json({ success: true });
    } catch (error) {
      console.error("Error deleting workflow:", error);
      res.status(500).json({ message: "Failed to delete workflow" });
    }
  });

  // History endpoint - unified view of executions and recordings
  app.get('/api/history', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const type = req.query.type as string;
      
      if (type === 'execution' || !type) {
        const tasks = await storage.getTasks(userId);
        const allExecutions = [];
        
        for (const task of tasks) {
          const executions = await storage.getExecutions(task.id, userId);
          allExecutions.push(...executions.map(exec => ({
            ...exec,
            type: 'execution',
            taskName: task.name,
          })));
        }
        
        if (type === 'execution') {
          allExecutions.sort((a, b) => 
            new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
          );
          return res.json(allExecutions);
        }
        
        const recordings = await storage.getRecordings(userId);
        const allHistory = [
          ...allExecutions,
          ...recordings.map(rec => ({ ...rec, type: 'recording' })),
        ];
        
        allHistory.sort((a: any, b: any) => {
          const aDate = new Date(a.startedAt || a.createdAt).getTime();
          const bDate = new Date(b.startedAt || b.createdAt).getTime();
          return bDate - aDate;
        });
        
        return res.json(allHistory);
      }
      
      if (type === 'recording') {
        const recordings = await storage.getRecordings(userId);
        return res.json(recordings.map(rec => ({ ...rec, type: 'recording' })));
      }
      
      res.status(400).json({ message: "Invalid type parameter" });
    } catch (error) {
      console.error("Error fetching history:", error);
      res.status(500).json({ message: "Failed to fetch history" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
