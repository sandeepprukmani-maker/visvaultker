import { CheckCircle2, XCircle, Loader2, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface ExecutionLog {
  timestamp: number;
  action: string;
  status: string;
  details?: any;
}

interface ExecutionResultsProps {
  status: "pending" | "running" | "success" | "error";
  logs?: ExecutionLog[];
  result?: any;
  error?: string;
  duration?: string;
  prompt: string;
}

export function ExecutionResults({
  status,
  logs = [],
  result,
  error,
  duration,
  prompt,
}: ExecutionResultsProps) {
  const statusConfig = {
    pending: {
      icon: Clock,
      label: "Pending",
      color: "bg-muted text-muted-foreground",
    },
    running: {
      icon: Loader2,
      label: "Running",
      color: "bg-primary/10 text-primary",
    },
    success: {
      icon: CheckCircle2,
      label: "Success",
      color: "bg-green-500/10 text-green-600 dark:text-green-400",
    },
    error: {
      icon: XCircle,
      label: "Error",
      color: "bg-destructive/10 text-destructive",
    },
  };

  const StatusIcon = statusConfig[status].icon;

  return (
    <Card className="w-full max-w-4xl mx-auto p-6" data-testid="card-execution-results">
      <div className="space-y-4">
        {/* Header with status */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-muted-foreground mb-1">Prompt</p>
            <p className="text-base font-medium truncate" data-testid="text-prompt">
              {prompt}
            </p>
          </div>
          
          <Badge
            variant="secondary"
            className={`${statusConfig[status].color} gap-1.5 px-3 py-1.5`}
            data-testid="badge-status"
          >
            <StatusIcon className={`h-3.5 w-3.5 ${status === "running" ? "animate-spin" : ""}`} />
            <span>{statusConfig[status].label}</span>
          </Badge>
        </div>

        {duration && (
          <div className="text-sm text-muted-foreground">
            Completed in {duration}
          </div>
        )}

        <Separator />

        {/* Logs */}
        {logs.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Execution Log</h4>
            <ScrollArea className="h-48 rounded-lg border bg-muted/30 p-4">
              <div className="space-y-2" data-testid="container-logs">
                {logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-3 text-sm">
                    <span className="text-xs text-muted-foreground font-mono whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium">{log.action}</p>
                      {log.details && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {JSON.stringify(log.details)}
                        </p>
                      )}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {log.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Result</h4>
            <ScrollArea className="max-h-64 rounded-lg border bg-muted/30 p-4">
              <pre className="text-xs font-mono" data-testid="text-result">
                {JSON.stringify(result, null, 2)}
              </pre>
            </ScrollArea>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
            <h4 className="text-sm font-semibold text-destructive mb-2">Error</h4>
            <p className="text-sm text-destructive" data-testid="text-error">
              {error}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
