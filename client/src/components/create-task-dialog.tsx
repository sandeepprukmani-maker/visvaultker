import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export function CreateTaskDialog() {
  const [open, setOpen] = useState(false);
  const [taskName, setTaskName] = useState("");
  const [description, setDescription] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const { toast } = useToast();

  const { data: profiles } = useQuery({
    queryKey: ["/api/python/api/website-profiles"],
    enabled: open,
  });

  const createTaskMutation = useMutation({
    mutationFn: async (data: any) => {
      return await apiRequest("/api/python/api/tasks/teach", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/python/api/tasks"] });
      queryClient.invalidateQueries({ queryKey: ["/api/python/api/analytics/overview"] });
      toast({
        title: "Task Created",
        description: "Your automation task has been created successfully.",
      });
      setOpen(false);
      setTaskName("");
      setDescription("");
      setWebsiteUrl("");
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to create task",
        variant: "destructive",
      });
    },
  });

  const handleCreate = () => {
    if (!taskName || !websiteUrl) {
      toast({
        title: "Missing Information",
        description: "Please provide task name and website URL",
        variant: "destructive",
      });
      return;
    }

    createTaskMutation.mutate({
      name: taskName,
      description: description || "No description provided",
      websiteUrl: websiteUrl,
      demonstration: [
        {
          type: "navigate",
          selector: "",
          value: websiteUrl,
          description: "Navigate to website",
        },
      ],
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-create-task">
          <Plus className="h-4 w-4 mr-2" />
          Create Task
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
          <DialogDescription>
            Create a new automation task. The AI will learn and generalize the actions.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="task-name">Task Name</Label>
            <Input
              id="task-name"
              placeholder="e.g., Send LinkedIn Connection Request"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              data-testid="input-task-name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this task should do..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[100px]"
              data-testid="input-task-description"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="website">Website URL</Label>
            <Input
              id="website"
              type="url"
              placeholder="https://example.com"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              data-testid="input-website-url"
            />
            {profiles && profiles.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Or select from {profiles.length} learned website{profiles.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => setOpen(false)}
            disabled={createTaskMutation.isPending}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleCreate} 
            disabled={createTaskMutation.isPending}
            data-testid="button-submit-task"
          >
            {createTaskMutation.isPending ? "Creating..." : "Create Task"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
