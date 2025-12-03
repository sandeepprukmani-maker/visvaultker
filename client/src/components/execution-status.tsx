import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Play, 
  Pause, 
  Square, 
  Loader2, 
  CheckCircle2, 
  XCircle,
  AlertCircle,
  Info,
  Terminal
} from "lucide-react";
import type { ExecutionStatus as ExecStatus, LogEntry } from "@shared/schema";

interface ExecutionStatusProps {
  status: ExecStatus;
  progress: number;
  currentStep?: string;
  logs: LogEntry[];
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  isControlling?: boolean;
}

const statusConfig: Record<ExecStatus, { label: string; color: string; icon: React.ReactNode }> = {
  planning: {
    label: "Planning",
    color: "bg-purple-500",
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
  },
  ready: {
    label: "Ready",
    color: "bg-blue-500",
    icon: <Play className="h-4 w-4" />,
  },
  running: {
    label: "Running",
    color: "bg-blue-500",
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
  },
  paused: {
    label: "Paused",
    color: "bg-yellow-500",
    icon: <Pause className="h-4 w-4" />,
  },
  completed: {
    label: "Completed",
    color: "bg-green-500",
    icon: <CheckCircle2 className="h-4 w-4" />,
  },
  failed: {
    label: "Failed",
    color: "bg-destructive",
    icon: <XCircle className="h-4 w-4" />,
  },
  cancelled: {
    label: "Cancelled",
    color: "bg-muted-foreground",
    icon: <Square className="h-4 w-4" />,
  },
};

const logLevelConfig = {
  info: { icon: Info, color: "text-blue-500" },
  warning: { icon: AlertCircle, color: "text-yellow-500" },
  error: { icon: XCircle, color: "text-destructive" },
  success: { icon: CheckCircle2, color: "text-green-500" },
};

export function ExecutionStatus({
  status,
  progress,
  currentStep,
  logs,
  onPause,
  onResume,
  onCancel,
  isControlling = false,
}: ExecutionStatusProps) {
  const config = statusConfig[status];
  const isRunning = status === "running";
  const isPaused = status === "paused";
  const isActive = isRunning || isPaused || status === "planning";
  const isFinished = status === "completed" || status === "failed" || status === "cancelled";

  return (
    <Card className="overflow-hidden" data-testid="card-execution-status">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 gap-4 pb-4">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.color} text-white`}
          >
            {config.icon}
          </div>
          <div>
            <CardTitle className="text-lg">Execution Status</CardTitle>
            <div className="flex items-center gap-2 mt-1">
              <Badge
                variant="secondary"
                className={`${config.color} text-white border-0`}
              >
                {config.label}
              </Badge>
              {currentStep && (
                <span className="text-sm text-muted-foreground">
                  Current: {currentStep}
                </span>
              )}
            </div>
          </div>
        </div>

        {isActive && (
          <div className="flex items-center gap-2">
            {isRunning && onPause && (
              <Button
                variant="outline"
                size="sm"
                onClick={onPause}
                disabled={isControlling}
                data-testid="button-pause-execution"
              >
                {isControlling ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Pause className="mr-2 h-4 w-4" />
                )}
                Pause
              </Button>
            )}
            {isPaused && onResume && (
              <Button
                variant="outline"
                size="sm"
                onClick={onResume}
                disabled={isControlling}
                data-testid="button-resume-execution"
              >
                {isControlling ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Resume
              </Button>
            )}
            {onCancel && (
              <Button
                variant="destructive"
                size="sm"
                onClick={onCancel}
                disabled={isControlling}
                data-testid="button-cancel-execution"
              >
                {isControlling ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Square className="mr-2 h-4 w-4" />
                )}
                Cancel
              </Button>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" data-testid="progress-execution" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Execution Logs</span>
          </div>
          <ScrollArea className="h-48 rounded-md border bg-muted/30 p-3">
            <div className="space-y-1 font-mono text-xs">
              {logs.length === 0 ? (
                <div className="text-muted-foreground italic">
                  No logs yet...
                </div>
              ) : (
                logs.map((log, index) => {
                  const LogIcon = logLevelConfig[log.level].icon;
                  return (
                    <div
                      key={index}
                      className="flex items-start gap-2"
                      data-testid={`log-entry-${index}`}
                    >
                      <LogIcon
                        className={`h-3.5 w-3.5 mt-0.5 shrink-0 ${logLevelConfig[log.level].color}`}
                      />
                      <span className="text-muted-foreground shrink-0">
                        {log.timestamp}
                      </span>
                      <span className={log.level === "error" ? "text-destructive" : ""}>
                        {log.message}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
}
