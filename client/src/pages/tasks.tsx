import { TaskCard } from "@/components/task-card";
import { CreateTaskDialog } from "@/components/create-task-dialog";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent } from "@/components/ui/card";

export default function Tasks() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const { toast } = useToast();

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["/api/python/api/tasks"],
  });

  const executeTaskMutation = useMutation({
    mutationFn: async (taskId: string) => {
      return await apiRequest(`/api/python/api/tasks/${taskId}/execute`, {
        method: "POST",
        body: JSON.stringify({ taskId, parameters: {} }),
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Task Execution Started",
        description: `Execution ID: ${data.executionId}`,
      });
      queryClient.invalidateQueries({ queryKey: ["/api/python/api/executions"] });
    },
    onError: (error: any) => {
      toast({
        title: "Execution Failed",
        description: error.message || "Failed to execute task",
        variant: "destructive",
      });
    },
  });

  const filteredTasks = (tasks || []).filter((task: any) => {
    const matchesSearch = task.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Task Library</h1>
          <p className="text-muted-foreground mt-1">
            Manage and execute your automation tasks
          </p>
        </div>
        <CreateTaskDialog />
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            data-testid="input-search-tasks"
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[180px]" data-testid="select-filter-status">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tasks</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="p-6 text-center">
            Loading tasks...
          </CardContent>
        </Card>
      ) : filteredTasks.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground mb-4">
              No tasks found. Create your first automation task to get started!
            </p>
            <CreateTaskDialog />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTasks.map((task: any) => (
            <TaskCard
              key={task.id}
              id={task.id}
              title={task.name}
              description={task.description || "No description"}
              website={task.website_url}
              lastRun="Recently"
              runCount={0}
              status="active"
              onRun={() => executeTaskMutation.mutate(task.id)}
              onEdit={() => toast({ title: "Edit feature coming soon!" })}
              onDelete={() => toast({ title: "Delete feature coming soon!" })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
