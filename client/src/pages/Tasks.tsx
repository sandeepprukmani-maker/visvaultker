import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Play, Code2, Loader2, Terminal, CheckCircle2, XCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Task, Execution } from "@shared/schema";

export default function Tasks() {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTaskOpen, setNewTaskOpen] = useState(false);
  const [newTaskName, setNewTaskName] = useState("");
  const [newTaskCode, setNewTaskCode] = useState("");
  const [newTaskLanguage, setNewTaskLanguage] = useState("typescript");
  const { toast } = useToast();

  const { data: tasks = [], isLoading } = useQuery<Task[]>({
    queryKey: ['/api/tasks'],
  });

  const { data: executions = [] } = useQuery<Execution[]>({
    queryKey: ['/api/executions'],
  });

  const createTask = useMutation({
    mutationFn: async (data: { name: string; code: string; language: string }) => {
      const res = await apiRequest('POST', '/api/tasks', {
        ...data,
        description: `Task created at ${new Date().toLocaleString()}`,
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/tasks'] });
      setNewTaskOpen(false);
      setNewTaskName("");
      setNewTaskCode("");
      toast({
        title: "Task created",
        description: "Your task has been created successfully",
      });
    },
  });

  const executeTask = useMutation({
    mutationFn: async (taskId: string) => {
      const res = await apiRequest('POST', `/api/tasks/${taskId}/execute`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/executions'] });
      toast({
        title: "Task executed",
        description: "Your task is running",
      });
    },
  });

  const deleteTask = useMutation({
    mutationFn: async (taskId: string) => {
      const res = await apiRequest('DELETE', `/api/tasks/${taskId}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/tasks'] });
      toast({
        title: "Task deleted",
        description: "Your task has been removed",
      });
    },
  });

  const handleCreateTask = () => {
    if (newTaskName.trim() && newTaskCode.trim()) {
      createTask.mutate({
        name: newTaskName.trim(),
        code: newTaskCode.trim(),
        language: newTaskLanguage,
      });
    }
  };

  const getTaskExecutions = (taskId: string) => {
    return executions.filter(exec => exec.taskId === taskId);
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any }> = {
      completed: { variant: 'default', icon: CheckCircle2 },
      failed: { variant: 'destructive', icon: XCircle },
      running: { variant: 'secondary', icon: Loader2 },
      pending: { variant: 'outline', icon: Loader2 },
    };

    const config = variants[status] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant}>
        <Icon className={`w-3 h-3 mr-1 ${status === 'running' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  return (
    <div className="h-screen overflow-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tasks</h1>
          <p className="text-muted-foreground">Manage and execute your automation scripts</p>
        </div>
        <Dialog open={newTaskOpen} onOpenChange={setNewTaskOpen}>
          <DialogTrigger asChild>
            <Button data-testid="button-new-task">
              <Plus className="w-4 h-4 mr-2" />
              New Task
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Task</DialogTitle>
              <DialogDescription>Add a new automation script to your task library</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Task Name</label>
                <Input
                  placeholder="e.g., Web Scraper, Form Automation"
                  value={newTaskName}
                  onChange={(e) => setNewTaskName(e.target.value)}
                  data-testid="input-task-name"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Language</label>
                <Select value={newTaskLanguage} onValueChange={setNewTaskLanguage}>
                  <SelectTrigger data-testid="select-language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="typescript">TypeScript</SelectItem>
                    <SelectItem value="javascript">JavaScript</SelectItem>
                    <SelectItem value="python">Python</SelectItem>
                    <SelectItem value="bash">Bash</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Code</label>
                <Textarea
                  placeholder="console.log('Hello AutoPilot Studio X!');"
                  value={newTaskCode}
                  onChange={(e) => setNewTaskCode(e.target.value)}
                  className="min-h-[200px] font-mono text-sm"
                  data-testid="input-task-code"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setNewTaskOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateTask}
                  disabled={!newTaskName.trim() || !newTaskCode.trim() || createTask.isPending}
                  data-testid="button-create-task"
                >
                  {createTask.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Create Task
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>All Tasks</CardTitle>
              <CardDescription>Your automation script library</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin" data-testid="loader-tasks" />
                </div>
              ) : tasks.length === 0 ? (
                <p className="text-center text-muted-foreground p-8" data-testid="text-no-tasks">
                  No tasks yet. Create your first automation script!
                </p>
              ) : (
                <ScrollArea className="h-[600px]">
                  <div className="space-y-3">
                    {tasks.map((task) => {
                      const taskExecs = getTaskExecutions(task.id);
                      const latestExec = taskExecs[0];
                      return (
                        <Card
                          key={task.id}
                          className={`hover-elevate cursor-pointer ${selectedTask?.id === task.id ? 'border-primary' : ''}`}
                          onClick={() => setSelectedTask(task)}
                          data-testid={`card-task-${task.id}`}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start gap-2">
                                  <Code2 className="w-4 h-4 mt-1 text-primary" />
                                  <div className="flex-1">
                                    <p className="font-medium" data-testid={`text-name-${task.id}`}>{task.name}</p>
                                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                      {task.description}
                                    </p>
                                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                                      <Badge variant="outline">{task.language}</Badge>
                                      {latestExec && getStatusBadge(latestExec.status)}
                                      <span className="text-xs text-muted-foreground">
                                        {taskExecs.length} execution{taskExecs.length !== 1 ? 's' : ''}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    executeTask.mutate(task.id);
                                  }}
                                  disabled={executeTask.isPending}
                                  data-testid={`button-run-${task.id}`}
                                >
                                  <Play className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
              <CardDescription>Task information and executions</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedTask ? (
                <div className="space-y-4" data-testid="task-details">
                  <div>
                    <h3 className="font-semibold mb-2">Name</h3>
                    <p className="text-sm">{selectedTask.name}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Language</h3>
                    <Badge variant="outline">{selectedTask.language}</Badge>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                      <Terminal className="w-4 h-4" />
                      Code
                    </h3>
                    <ScrollArea className="h-[200px]">
                      <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                        {selectedTask.code}
                      </pre>
                    </ScrollArea>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Recent Executions</h3>
                    <div className="space-y-2">
                      {getTaskExecutions(selectedTask.id).slice(0, 5).map((exec) => (
                        <div key={exec.id} className="flex items-center justify-between text-sm p-2 bg-muted rounded-md">
                          <span>{getStatusBadge(exec.status)}</span>
                          {exec.duration && <span className="text-muted-foreground">{exec.duration}ms</span>}
                        </div>
                      ))}
                      {getTaskExecutions(selectedTask.id).length === 0 && (
                        <p className="text-sm text-muted-foreground">No executions yet</p>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="w-full"
                    onClick={() => deleteTask.mutate(selectedTask.id)}
                    disabled={deleteTask.isPending}
                    data-testid="button-delete-task"
                  >
                    {deleteTask.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Delete Task
                  </Button>
                </div>
              ) : (
                <p className="text-center text-muted-foreground p-8">
                  Select a task to view details
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
