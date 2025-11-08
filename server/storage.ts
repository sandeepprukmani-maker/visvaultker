import { 
  type User, 
  type InsertUser,
  type UpsertUser,
  type Task,
  type InsertTask,
  type Execution,
  type InsertExecution,
  type Recording,
  type InsertRecording,
  type Workflow,
  type InsertWorkflow
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // User operations
  getUser(id: string): Promise<User | undefined>;
  getUserByEmail(email: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Task operations
  getTasks(userId: string): Promise<Task[]>;
  getTask(id: string, userId: string): Promise<Task | undefined>;
  createTask(task: InsertTask): Promise<Task>;
  updateTask(id: string, userId: string, task: Partial<InsertTask>): Promise<Task | undefined>;
  deleteTask(id: string, userId: string): Promise<boolean>;
  
  // Execution operations
  getExecutions(taskId: string, userId: string): Promise<Execution[]>;
  getExecution(id: string, userId: string): Promise<Execution | undefined>;
  createExecution(execution: InsertExecution): Promise<Execution>;
  updateExecution(id: string, userId: string, execution: Partial<InsertExecution>): Promise<Execution | undefined>;
  
  // Recording operations
  getRecordings(userId: string): Promise<Recording[]>;
  getRecording(id: string, userId: string): Promise<Recording | undefined>;
  createRecording(recording: InsertRecording): Promise<Recording>;
  deleteRecording(id: string, userId: string): Promise<boolean>;
  
  // Workflow operations
  getWorkflows(userId: string): Promise<Workflow[]>;
  getWorkflow(id: string, userId: string): Promise<Workflow | undefined>;
  createWorkflow(workflow: InsertWorkflow): Promise<Workflow>;
  updateWorkflow(id: string, userId: string, workflow: Partial<InsertWorkflow>): Promise<Workflow | undefined>;
  deleteWorkflow(id: string, userId: string): Promise<boolean>;
  updateRecording(id: string, userId: string, recording: Partial<InsertRecording>): Promise<Recording | undefined>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private tasks: Map<string, Task>;
  private executions: Map<string, Execution>;
  private recordings: Map<string, Recording>;
  private workflows: Map<string, Workflow>;

  constructor() {
    this.users = new Map();
    this.tasks = new Map();
    this.executions = new Map();
    this.recordings = new Map();
    this.workflows = new Map();
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByEmail(email: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.email === email);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const now = new Date();
    const user: User = {
      email: null,
      firstName: null,
      lastName: null,
      profileImageUrl: null,
      ...insertUser,
      id: id,
      createdAt: now,
      updatedAt: now
    };
    this.users.set(id, user);
    return user;
  }

  async upsertUser(upsertUser: UpsertUser): Promise<User> {
    const existingUser = upsertUser.id ? this.users.get(upsertUser.id) : undefined;
    const id = upsertUser.id || randomUUID();
    const now = new Date();
    const user: User = {
      email: null,
      firstName: null,
      lastName: null,
      profileImageUrl: null,
      ...existingUser,
      ...upsertUser,
      id,
      createdAt: existingUser?.createdAt || now,
      updatedAt: now,
    };
    this.users.set(id, user);
    return user;
  }

  async getTasks(userId: string): Promise<Task[]> {
    return Array.from(this.tasks.values()).filter(task => task.userId === userId);
  }

  async getTask(id: string, userId: string): Promise<Task | undefined> {
    const task = this.tasks.get(id);
    if (!task || task.userId !== userId) return undefined;
    return task;
  }

  async createTask(insertTask: InsertTask): Promise<Task> {
    const id = randomUUID();
    const now = new Date();
    const task: Task = {
      description: null,
      prompt: null,
      language: "typescript",
      ...insertTask,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.tasks.set(id, task);
    return task;
  }

  async updateTask(id: string, userId: string, update: Partial<InsertTask>): Promise<Task | undefined> {
    const task = this.tasks.get(id);
    if (!task || task.userId !== userId) return undefined;
    
    const updated: Task = {
      ...task,
      ...update,
      updatedAt: new Date(),
    };
    this.tasks.set(id, updated);
    return updated;
  }

  async deleteTask(id: string, userId: string): Promise<boolean> {
    const task = this.tasks.get(id);
    if (!task || task.userId !== userId) return false;
    return this.tasks.delete(id);
  }

  async getExecutions(taskId: string, userId: string): Promise<Execution[]> {
    return Array.from(this.executions.values()).filter(
      exec => exec.taskId === taskId && exec.userId === userId
    );
  }

  async getExecution(id: string, userId: string): Promise<Execution | undefined> {
    const execution = this.executions.get(id);
    if (!execution || execution.userId !== userId) return undefined;
    return execution;
  }

  async createExecution(insertExecution: InsertExecution): Promise<Execution> {
    const id = randomUUID();
    const execution: Execution = {
      status: "pending",
      ...insertExecution,
      id,
      startedAt: new Date(),
      finishedAt: null,
      duration: null,
      logs: null,
      error: null,
      screenshotUrls: null,
    };
    this.executions.set(id, execution);
    return execution;
  }

  async updateExecution(id: string, userId: string, update: Partial<InsertExecution>): Promise<Execution | undefined> {
    const execution = this.executions.get(id);
    if (!execution || execution.userId !== userId) return undefined;
    
    const updated: Execution = {
      ...execution,
      ...update,
    };
    this.executions.set(id, updated);
    return updated;
  }

  async getRecordings(userId: string): Promise<Recording[]> {
    return Array.from(this.recordings.values()).filter(rec => rec.userId === userId);
  }

  async getRecording(id: string, userId: string): Promise<Recording | undefined> {
    const recording = this.recordings.get(id);
    if (!recording || recording.userId !== userId) return undefined;
    return recording;
  }

  async createRecording(insertRecording: InsertRecording): Promise<Recording> {
    const id = randomUUID();
    const recording: Recording = {
      duration: null,
      generatedCode: null,
      language: "typescript",
      status: "recording",
      ...insertRecording,
      id,
      createdAt: new Date(),
    };
    this.recordings.set(id, recording);
    return recording;
  }

  async updateRecording(id: string, userId: string, update: Partial<InsertRecording>): Promise<Recording | undefined> {
    const recording = this.recordings.get(id);
    if (!recording || recording.userId !== userId) return undefined;
    
    const updated: Recording = {
      ...recording,
      ...update,
    };
    this.recordings.set(id, updated);
    return updated;
  }

  async deleteRecording(id: string, userId: string): Promise<boolean> {
    const recording = this.recordings.get(id);
    if (!recording || recording.userId !== userId) return false;
    return this.recordings.delete(id);
  }

  async getWorkflows(userId: string): Promise<Workflow[]> {
    return Array.from(this.workflows.values()).filter(wf => wf.userId === userId);
  }

  async getWorkflow(id: string, userId: string): Promise<Workflow | undefined> {
    const workflow = this.workflows.get(id);
    if (!workflow || workflow.userId !== userId) return undefined;
    return workflow;
  }

  async createWorkflow(insertWorkflow: InsertWorkflow): Promise<Workflow> {
    const id = randomUUID();
    const now = new Date();
    const workflow: Workflow = {
      description: null,
      ...insertWorkflow,
      id,
      createdAt: now,
      updatedAt: now,
    };
    this.workflows.set(id, workflow);
    return workflow;
  }

  async updateWorkflow(id: string, userId: string, update: Partial<InsertWorkflow>): Promise<Workflow | undefined> {
    const workflow = this.workflows.get(id);
    if (!workflow || workflow.userId !== userId) return undefined;
    
    const updated: Workflow = {
      ...workflow,
      ...update,
      updatedAt: new Date(),
    };
    this.workflows.set(id, updated);
    return updated;
  }

  async deleteWorkflow(id: string, userId: string): Promise<boolean> {
    const workflow = this.workflows.get(id);
    if (!workflow || workflow.userId !== userId) return false;
    return this.workflows.delete(id);
  }
}

export const storage = new MemStorage();
