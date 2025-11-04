import { TaskCard } from "@/components/task-card";
import { CreateTaskDialog } from "@/components/create-task-dialog";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";

export default function Tasks() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  // todo: remove mock data
  const tasks = [
    {
      id: "task-1",
      title: "Send LinkedIn Connection",
      description: "Connect with professionals based on search criteria",
      website: "linkedin.com",
      lastRun: "2 hours ago",
      runCount: 15,
      status: "active" as const,
    },
    {
      id: "task-2",
      title: "Scrape Product Prices",
      description: "Extract pricing data from e-commerce sites",
      website: "amazon.com",
      lastRun: "1 day ago",
      runCount: 42,
      status: "active" as const,
    },
    {
      id: "task-3",
      title: "Twitter Auto Reply",
      description: "Automatically reply to mentions with custom messages",
      website: "twitter.com",
      lastRun: "3 days ago",
      runCount: 8,
      status: "draft" as const,
    },
    {
      id: "task-4",
      title: "Extract GitHub Stars",
      description: "Get list of users who starred a repository",
      website: "github.com",
      lastRun: "1 week ago",
      runCount: 23,
      status: "disabled" as const,
    },
    {
      id: "task-5",
      title: "Monitor Job Postings",
      description: "Track new job listings matching criteria",
      website: "linkedin.com",
      lastRun: "4 hours ago",
      runCount: 67,
      status: "active" as const,
    },
    {
      id: "task-6",
      title: "Form Auto-Fill",
      description: "Automatically fill and submit web forms",
      website: "forms.google.com",
      runCount: 0,
      status: "draft" as const,
    },
  ];

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

      {/* Filters */}
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
            <SelectItem value="disabled">Disabled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Task Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            {...task}
            onRun={() => console.log("Run task", task.id)}
            onEdit={() => console.log("Edit task", task.id)}
            onDelete={() => console.log("Delete task", task.id)}
          />
        ))}
      </div>
    </div>
  );
}
