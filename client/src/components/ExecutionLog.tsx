import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Clock, ArrowRight } from "lucide-react";

export interface LogEntry {
  id: string;
  timestamp: number;
  action: string;
  status: "success" | "error" | "pending" | "running";
  selector?: string;
  description?: string;
}

interface ExecutionLogProps {
  entries: LogEntry[];
  detectedUrl?: string;
  usedModes?: string[];
}

export default function ExecutionLog({ entries, detectedUrl, usedModes }: ExecutionLogProps) {
  const getStatusIcon = (status: LogEntry["status"]) => {
    switch (status) {
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-destructive" />;
      case "running":
        return <ArrowRight className="h-4 w-4 animate-pulse text-primary" />;
      case "pending":
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: LogEntry["status"]) => {
    const variants = {
      success: "bg-green-500/10 text-green-500 border-green-500/20",
      error: "bg-destructive/10 text-destructive border-destructive/20",
      running: "bg-primary/10 text-primary border-primary/20",
      pending: "bg-muted text-muted-foreground border-muted-foreground/20",
    };
    
    return (
      <Badge variant="outline" className={variants[status]} data-testid={`badge-${status}`}>
        {status}
      </Badge>
    );
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <Card className="flex h-full flex-col border">
      <div className="flex h-10 items-center justify-between border-b px-4">
        <h3 className="text-sm font-medium">Execution Log</h3>
        {usedModes && usedModes.length > 0 && (
          <div className="flex gap-1">
            {usedModes.map((mode) => (
              <Badge key={mode} variant="outline" className="text-xs">
                {mode}
              </Badge>
            ))}
          </div>
        )}
      </div>
      {detectedUrl && (
        <div className="border-b px-4 py-2 bg-muted/30">
          <p className="text-xs text-muted-foreground">Detected URL:</p>
          <code className="text-xs font-mono">{detectedUrl}</code>
        </div>
      )}
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {entries.length === 0 ? (
            <div className="flex h-32 items-center justify-center">
              <p className="text-sm text-muted-foreground">No actions executed yet</p>
            </div>
          ) : (
            entries.map((entry, index) => (
              <div
                key={entry.id}
                className="group relative rounded-md border border-transparent p-3 hover-elevate"
                data-testid={`log-entry-${index}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getStatusIcon(entry.status)}</div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">
                        {formatTime(entry.timestamp)}
                      </span>
                      {getStatusBadge(entry.status)}
                    </div>
                    <p className="text-sm font-medium">{entry.action}</p>
                    {entry.description && (
                      <p className="text-xs text-muted-foreground">{entry.description}</p>
                    )}
                    {entry.selector && (
                      <code className="block rounded bg-muted px-2 py-1 font-mono text-xs">
                        {entry.selector}
                      </code>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
