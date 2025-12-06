import { type AutomationTask } from "@shared/schema";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Loader2, Clock } from "lucide-react";

interface HistoryItemProps {
  task: AutomationTask;
  isActive?: boolean;
  onClick: () => void;
}

function getStatusBadge(status: string) {
  switch (status) {
    case "success":
      return (
        <Badge variant="outline" className="gap-1 border-emerald-500/50 text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="h-3 w-3" />
          Done
        </Badge>
      );
    case "error":
      return (
        <Badge variant="outline" className="gap-1 border-destructive/50 text-destructive">
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    case "running":
      return (
        <Badge variant="outline" className="gap-1 border-primary/50 text-primary">
          <Loader2 className="h-3 w-3 animate-spin" />
          Running
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className="gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>
      );
  }
}

export function HistoryItem({ task, isActive, onClick }: HistoryItemProps) {
  const time = new Date(task.createdAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const date = new Date(task.createdAt).toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-3 rounded-md transition-colors hover-elevate active-elevate-2",
        isActive && "bg-accent"
      )}
      data-testid={`history-item-${task.id}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <p className="text-sm font-medium line-clamp-2 flex-1">{task.prompt}</p>
      </div>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">
          {date} {time}
        </span>
        {getStatusBadge(task.status)}
      </div>
    </button>
  );
}
