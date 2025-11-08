import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { insertTaskSchema, insertExecutionSchema, insertRecordingSchema, insertWorkflowSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Set up auth middleware and routes
  await setupAuth(app);

  // Auth user endpoint
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
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
  app.get('/api/tasks', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const tasks = await storage.getTasks(userId);
      res.json(tasks);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      res.status(500).json({ message: "Failed to fetch tasks" });
    }
  });

  app.post('/api/tasks', isAuthenticated, async (req: any, res) => {
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

  app.get('/api/tasks/:id', isAuthenticated, async (req: any, res) => {
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

  app.patch('/api/tasks/:id', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const task = await storage.updateTask(req.params.id, userId, req.body);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      res.json(task);
    } catch (error) {
      console.error("Error updating task:", error);
      res.status(500).json({ message: "Failed to update task" });
    }
  });

  app.delete('/api/tasks/:id', isAuthenticated, async (req: any, res) => {
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
  app.get('/api/tasks/:taskId/executions', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const executions = await storage.getExecutions(req.params.taskId, userId);
      res.json(executions);
    } catch (error) {
      console.error("Error fetching executions:", error);
      res.status(500).json({ message: "Failed to fetch executions" });
    }
  });

  app.post('/api/tasks/:taskId/execute', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      // Verify task ownership before creating execution
      const task = await storage.getTask(req.params.taskId, userId);
      if (!task) {
        return res.status(404).json({ message: "Task not found" });
      }
      
      const validation = insertExecutionSchema.safeParse({
        taskId: req.params.taskId,
        userId,
        status: "pending",
      });
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid execution data", errors: validation.error.errors });
      }
      
      const execution = await storage.createExecution(validation.data);
      res.json(execution);
    } catch (error) {
      console.error("Error creating execution:", error);
      res.status(500).json({ message: "Failed to create execution" });
    }
  });

  // Recording routes
  app.get('/api/recordings', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const recordings = await storage.getRecordings(userId);
      res.json(recordings);
    } catch (error) {
      console.error("Error fetching recordings:", error);
      res.status(500).json({ message: "Failed to fetch recordings" });
    }
  });

  app.post('/api/recordings', isAuthenticated, async (req: any, res) => {
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

  app.delete('/api/recordings/:id', isAuthenticated, async (req: any, res) => {
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
  app.get('/api/workflows', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const workflows = await storage.getWorkflows(userId);
      res.json(workflows);
    } catch (error) {
      console.error("Error fetching workflows:", error);
      res.status(500).json({ message: "Failed to fetch workflows" });
    }
  });

  app.post('/api/workflows', isAuthenticated, async (req: any, res) => {
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

  app.patch('/api/workflows/:id', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const workflow = await storage.updateWorkflow(req.params.id, userId, req.body);
      if (!workflow) {
        return res.status(404).json({ message: "Workflow not found" });
      }
      res.json(workflow);
    } catch (error) {
      console.error("Error updating workflow:", error);
      res.status(500).json({ message: "Failed to update workflow" });
    }
  });

  app.delete('/api/workflows/:id', isAuthenticated, async (req: any, res) => {
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

  const httpServer = createServer(app);
  return httpServer;
}
