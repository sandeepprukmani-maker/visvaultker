import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, Loader2, Info } from "lucide-react";

interface LogEntry {
  timestamp: string;
  level: "info" | "success" | "error" | "loading";
  message: string;
}

interface ExecutionLogProps {
  logs: LogEntry[];
}

export function ExecutionLog({ logs }: ExecutionLogProps) {
  const getIcon = (level: LogEntry["level"]) => {
    switch (level) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
      case "loading":
        return <Loader2 className="h-4 w-4 text-blue-600 dark:text-blue-400 animate-spin" />;
      default:
        return <Info className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getLevelColor = (level: LogEntry["level"]) => {
    switch (level) {
      case "success":
        return "text-green-700 dark:text-green-300";
      case "error":
        return "text-red-700 dark:text-red-300";
      case "loading":
        return "text-blue-700 dark:text-blue-300";
      default:
        return "text-foreground";
    }
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2 p-4 font-mono text-sm" data-testid="execution-log">
        {logs.map((log, index) => (
          <div key={index} className="flex items-start gap-3 p-2 rounded hover-elevate">
            {getIcon(log.level)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-muted-foreground">{log.timestamp}</span>
                <Badge variant="outline" className="text-xs">
                  {log.level}
                </Badge>
              </div>
              <p className={`text-sm ${getLevelColor(log.level)} break-words`}>
                {log.message}
              </p>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
