import { useState } from "react";
import { Search, Plus } from "lucide-react";
import { TaskCard } from "@/components/TaskCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Todo: remove mock data
const mockTasks = [
  {
    id: "1",
    name: "Amazon Product Search",
    description: "Searches for products on Amazon and extracts pricing information with screenshots of the first 5 results",
    language: "TypeScript",
    status: "success" as const,
    lastRun: "2 hours ago",
  },
  {
    id: "2",
    name: "LinkedIn Profile Scraper",
    description: "Extracts public profile information including job history and connections",
    language: "JavaScript",
    status: "failed" as const,
    lastRun: "1 day ago",
  },
  {
    id: "3",
    name: "Twitter Sentiment Analysis",
    description: "Monitors Twitter hashtags and performs sentiment analysis on recent tweets",
    language: "TypeScript",
    status: "success" as const,
    lastRun: "5 hours ago",
  },
  {
    id: "4",
    name: "E-commerce Price Monitor",
    description: "Tracks product prices across multiple e-commerce sites and sends alerts on price drops",
    language: "TypeScript",
    status: "pending" as const,
    lastRun: "Never",
  },
  {
    id: "5",
    name: "Form Auto-Fill Test",
    description: "Tests form validation by automatically filling and submitting test data",
    language: "JavaScript",
    status: "success" as const,
    lastRun: "30 minutes ago",
  },
  {
    id: "6",
    name: "Website Screenshot Generator",
    description: "Takes full-page screenshots of multiple URLs for visual regression testing",
    language: "TypeScript",
    status: "success" as const,
    lastRun: "3 days ago",
  },
];

export default function Tasks() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTasks = mockTasks.filter(task =>
    task.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-10"
              data-testid="input-search-tasks"
            />
          </div>
          <Button data-testid="button-new-task">
            <Plus className="w-4 h-4 mr-2" />
            New Task
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              {...task}
              onRun={() => console.log('Run task', task.id)}
              onEdit={() => console.log('Edit task', task.id)}
              onDelete={() => console.log('Delete task', task.id)}
              onDuplicate={() => console.log('Duplicate task', task.id)}
            />
          ))}
        </div>
        {filteredTasks.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <p className="text-sm text-muted-foreground">No tasks found</p>
          </div>
        )}
      </div>
    </div>
  );
}
