import { type AutomationTask } from "@shared/schema";
import { HistoryItem } from "./history-item";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Search, History, Trash2 } from "lucide-react";
import { useState } from "react";

interface HistorySidebarProps {
  tasks: AutomationTask[];
  activeTaskId?: string;
  onTaskSelect: (task: AutomationTask) => void;
  onClearHistory: () => void;
}

export function HistorySidebar({
  tasks,
  activeTaskId,
  onTaskSelect,
  onClearHistory,
}: HistorySidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTasks = tasks.filter((task) =>
    task.prompt?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full bg-sidebar">
      <div className="flex items-center justify-between gap-2 p-4 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">History</h2>
        </div>
        {tasks.length > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8"
                data-testid="button-clear-history"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear History</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to clear all automation history? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel data-testid="button-cancel-clear">Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={onClearHistory}
                  data-testid="button-confirm-clear"
                >
                  Clear All
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {tasks.length > 0 && (
        <div className="p-3 border-b border-sidebar-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 bg-background"
              data-testid="input-search-history"
            />
          </div>
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="p-2">
          {filteredTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <History className="h-8 w-8 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                {tasks.length === 0
                  ? "No automation history yet"
                  : "No matching tasks found"}
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {filteredTasks.map((task) => (
                <HistoryItem
                  key={task.id}
                  task={task}
                  isActive={task.id === activeTaskId}
                  onClick={() => onTaskSelect(task)}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
