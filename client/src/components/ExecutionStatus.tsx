import { CheckCircle2, XCircle, Loader2, Circle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ExecutionStep {
  id: string;
  action: string;
  status: "pending" | "running" | "completed" | "failed";
  duration?: string;
  timestamp?: string;
}

interface ExecutionStatusProps {
  steps: ExecutionStep[];
  currentStep?: number;
}

export function ExecutionStatus({ steps, currentStep = 0 }: ExecutionStatusProps) {
  const getStatusIcon = (status: ExecutionStep["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-destructive" />;
      case "running":
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      default:
        return <Circle className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: ExecutionStep["status"]) => {
    const variants = {
      completed: "default",
      failed: "destructive",
      running: "default",
      pending: "secondary",
    } as const;

    return (
      <Badge variant={variants[status]} className="text-xs capitalize">
        {status}
      </Badge>
    );
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Execution Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-center gap-3 p-2 rounded-md ${
              index === currentStep ? 'bg-accent/50' : ''
            }`}
            data-testid={`execution-step-${step.id}`}
          >
            {getStatusIcon(step.status)}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{step.action}</p>
              {step.timestamp && (
                <p className="text-xs text-muted-foreground">{step.timestamp}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {step.duration && (
                <span className="text-xs text-muted-foreground">{step.duration}</span>
              )}
              {getStatusBadge(step.status)}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
