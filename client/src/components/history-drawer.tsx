import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Clock,
  ChevronRight,
  Trash2,
  History
} from "lucide-react";
import { useState } from "react";
import type { Execution, ExecutionStatus } from "@shared/schema";

interface HistoryDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  executions: Execution[];
  onSelectExecution: (execution: Execution) => void;
  onDeleteExecution?: (id: string) => void;
  isLoading?: boolean;
}

const statusConfig: Record<ExecutionStatus, { icon: React.ReactNode; color: string; bgColor: string }> = {
  planning: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  ready: {
    icon: <Clock className="h-4 w-4" />,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  running: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  paused: {
    icon: <Clock className="h-4 w-4" />,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
  },
  completed: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
  failed: {
    icon: <XCircle className="h-4 w-4" />,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
  },
  cancelled: {
    icon: <XCircle className="h-4 w-4" />,
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
};

type FilterStatus = "all" | "completed" | "failed" | "running";

export function HistoryDrawer({
  open,
  onOpenChange,
  executions,
  onSelectExecution,
  onDeleteExecution,
  isLoading = false,
}: HistoryDrawerProps) {
  const [filter, setFilter] = useState<FilterStatus>("all");

  const filteredExecutions = executions.filter((exec) => {
    if (filter === "all") return true;
    if (filter === "running") return exec.status === "running" || exec.status === "planning" || exec.status === "paused";
    return exec.status === filter;
  });

  const formatDate = (date: Date | string | null) => {
    if (!date) return "Unknown";
    const d = new Date(date);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const truncatePrompt = (prompt: string, maxLength = 60) => {
    if (prompt.length <= maxLength) return prompt;
    return prompt.slice(0, maxLength) + "...";
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md" data-testid="drawer-history">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Execution History
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <Tabs value={filter} onValueChange={(v) => setFilter(v as FilterStatus)}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all" data-testid="tab-filter-all">All</TabsTrigger>
              <TabsTrigger value="completed" data-testid="tab-filter-completed">Success</TabsTrigger>
              <TabsTrigger value="failed" data-testid="tab-filter-failed">Failed</TabsTrigger>
              <TabsTrigger value="running" data-testid="tab-filter-running">Active</TabsTrigger>
            </TabsList>
          </Tabs>

          <ScrollArea className="h-[calc(100vh-200px)]">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">Loading history...</p>
              </div>
            ) : filteredExecutions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <History className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="mt-4 font-medium">No executions found</p>
                <p className="text-sm text-muted-foreground">
                  {filter === "all"
                    ? "Start your first automation"
                    : `No ${filter} executions yet`}
                </p>
              </div>
            ) : (
              <div className="space-y-2 pr-4">
                {filteredExecutions.map((execution) => {
                  const config = statusConfig[execution.status as ExecutionStatus];
                  return (
                    <div
                      key={execution.id}
                      className="group flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50 cursor-pointer"
                      onClick={() => onSelectExecution(execution)}
                      data-testid={`history-item-${execution.id}`}
                    >
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${config.bgColor}`}
                      >
                        <span className={config.color}>{config.icon}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">
                          {truncatePrompt(execution.prompt)}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            variant="secondary"
                            className={`text-xs ${config.color} ${config.bgColor} border-0`}
                          >
                            {execution.status}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(execution.createdAt)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {onDeleteExecution && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteExecution(execution.id);
                            }}
                            data-testid={`button-delete-${execution.id}`}
                          >
                            <Trash2 className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        )}
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>
      </SheetContent>
    </Sheet>
  );
}
