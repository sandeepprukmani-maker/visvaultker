import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus } from "lucide-react";
import { useState } from "react";

export function CreateTaskDialog() {
  const [open, setOpen] = useState(false);
  const [taskName, setTaskName] = useState("");
  const [description, setDescription] = useState("");
  const [website, setWebsite] = useState("");

  const handleCreate = () => {
    console.log("Creating task:", { taskName, description, website });
    setOpen(false);
    setTaskName("");
    setDescription("");
    setWebsite("");
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
            Teach the AI a new automation task using natural language
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
              placeholder="Describe what this task should do in natural language..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[100px]"
              data-testid="input-task-description"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="website">Target Website</Label>
            <Select value={website} onValueChange={setWebsite}>
              <SelectTrigger id="website" data-testid="select-website">
                <SelectValue placeholder="Select a learned website" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="linkedin.com">linkedin.com</SelectItem>
                <SelectItem value="twitter.com">twitter.com</SelectItem>
                <SelectItem value="amazon.com">amazon.com</SelectItem>
                <SelectItem value="github.com">github.com</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} data-testid="button-submit-task">
            Create Task
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
