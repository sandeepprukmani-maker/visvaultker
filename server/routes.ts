import type { Express, RequestHandler } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { 
  insertTaskSchema, 
  insertExecutionSchema, 
  insertRecordingSchema, 
  insertWorkflowSchema, 
  insertVoiceRequestSchema,
  updateTaskSchema,
  updateExecutionSchema,
  updateRecordingSchema,
  updateWorkflowSchema,
  updateVoiceRequestSchema
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
      let code = `// Auto-generated code from recording: ${recording.name}\n\n`;
      
      actions.forEach((action, index) => {
        if (action.type === 'click') {
          code += `// Step ${index + 1}: Click on ${action.selector || 'element'}\n`;
          code += `document.querySelector('${action.selector}')?.click();\n\n`;
        } else if (action.type === 'input') {
          code += `// Step ${index + 1}: Type "${action.value}" into ${action.selector}\n`;
          code += `const input${index} = document.querySelector('${action.selector}') as HTMLInputElement;\n`;
          code += `if (input${index}) input${index}.value = '${action.value}';\n\n`;
        } else if (action.type === 'navigate') {
          code += `// Step ${index + 1}: Navigate to ${action.url}\n`;
          code += `window.location.href = '${action.url}';\n\n`;
        }
      });
      
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

  // Voice Request routes
  app.get('/api/voice-requests', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const voiceRequests = await storage.getVoiceRequests(userId);
      res.json(voiceRequests);
    } catch (error) {
      console.error("Error fetching voice requests:", error);
      res.status(500).json({ message: "Failed to fetch voice requests" });
    }
  });

  app.post('/api/voice-requests', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = insertVoiceRequestSchema.safeParse({ 
        ...req.body, 
        userId,
        status: "pending",
      });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid voice request data", errors: validation.error.errors });
      }
      const voiceRequest = await storage.createVoiceRequest(validation.data);
      res.json(voiceRequest);
    } catch (error) {
      console.error("Error creating voice request:", error);
      res.status(500).json({ message: "Failed to create voice request" });
    }
  });

  app.post('/api/voice-requests/:id/generate', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const voiceRequest = await storage.getVoiceRequest(req.params.id, userId);
      if (!voiceRequest) {
        return res.status(404).json({ message: "Voice request not found" });
      }
      
      if (!voiceRequest.transcript) {
        return res.status(400).json({ message: "No transcript available to generate code from" });
      }
      
      const generatedCode = `// Generated from voice request: "${voiceRequest.transcript}"\n\nconsole.log("Hello from AutoPilot Studio X!");\n// TODO: Implement based on: ${voiceRequest.transcript}`;
      
      const task = await storage.createTask({
        userId,
        name: `Voice Task: ${voiceRequest.transcript.substring(0, 50)}...`,
        description: `Auto-generated from voice request`,
        code: generatedCode,
        language: voiceRequest.language || "typescript",
        prompt: voiceRequest.transcript,
      });
      
      await storage.updateVoiceRequest(req.params.id, userId, {
        status: "completed",
        generatedCode,
        taskId: task.id,
        processedAt: new Date(),
      });
      
      const updated = await storage.getVoiceRequest(req.params.id, userId);
      res.json(updated);
    } catch (error) {
      console.error("Error generating code:", error);
      res.status(500).json({ message: "Failed to generate code" });
    }
  });

  app.patch('/api/voice-requests/:id', authMiddleware, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const validation = updateVoiceRequestSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid voice request data", errors: validation.error.errors });
      }
      const voiceRequest = await storage.updateVoiceRequest(req.params.id, userId, validation.data);
      if (!voiceRequest) {
        return res.status(404).json({ message: "Voice request not found" });
      }
      res.json(voiceRequest);
    } catch (error) {
      console.error("Error updating voice request:", error);
      res.status(500).json({ message: "Failed to update voice request" });
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
