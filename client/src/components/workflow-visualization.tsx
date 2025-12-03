import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, 
  Circle, 
  Loader2, 
  XCircle, 
  Pause,
  ArrowRight,
  Globe,
  FileText,
  Search,
  Database,
  Code,
  Bot,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Workflow, WorkflowStep } from "@shared/schema";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

interface WorkflowVisualizationProps {
  workflow: Workflow | null;
  currentStepId?: string;
}

const statusConfig = {
  pending: {
    icon: Circle,
    color: "text-muted-foreground",
    bgColor: "bg-muted",
    label: "Pending",
  },
  running: {
    icon: Loader2,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    label: "Running",
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Completed",
  },
  failed: {
    icon: XCircle,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
    label: "Failed",
  },
  paused: {
    icon: Pause,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    label: "Paused",
  },
};

const toolIcons: Record<string, React.ReactNode> = {
  browser: <Globe className="h-4 w-4" />,
  file: <FileText className="h-4 w-4" />,
  search: <Search className="h-4 w-4" />,
  database: <Database className="h-4 w-4" />,
  code: <Code className="h-4 w-4" />,
  default: <Bot className="h-4 w-4" />,
};

function StepNode({ step, isActive, isLast, index }: { step: WorkflowStep; isActive: boolean; isLast: boolean; index: number }) {
  const config = statusConfig[step.status];
  const StatusIcon = config.icon;
  const toolIcon = toolIcons[step.tool || "default"] || toolIcons.default;

  return (
    <div className="flex items-start gap-3" data-testid={`workflow-step-${step.id}`}>
      <div className="flex flex-col items-center">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
            isActive
              ? "border-purple-500 bg-purple-500/10"
              : step.status === "completed"
              ? "border-green-500 bg-green-500/10"
              : step.status === "failed"
              ? "border-destructive bg-destructive/10"
              : "border-border bg-muted"
          }`}
          data-testid={`step-icon-${step.id}`}
        >
          <StatusIcon
            className={`h-5 w-5 ${config.color} ${config.animate ? "animate-spin" : ""}`}
          />
        </div>
        {!isLast && (
          <div className="h-8 w-0.5 bg-border" />
        )}
      </div>
      
      <div className="flex-1 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium" data-testid={`step-name-${step.id}`}>{step.name}</span>
          {step.tool && (
            <Badge variant="secondary" className="text-xs" data-testid={`step-tool-${step.id}`}>
              {toolIcon}
              <span className="ml-1 capitalize">{step.tool}</span>
            </Badge>
          )}
          <Badge
            variant="outline"
            className={`text-xs ${config.color}`}
            data-testid={`step-status-${step.id}`}
          >
            {config.label}
          </Badge>
        </div>
        {step.description && (
          <p className="mt-1 text-sm text-muted-foreground" data-testid={`step-description-${step.id}`}>{step.description}</p>
        )}
        {step.result && step.status === "completed" && (
          <div className="mt-2 rounded-md bg-green-500/5 p-2 text-sm text-green-700 dark:text-green-400" data-testid={`step-result-${step.id}`}>
            {step.result}
          </div>
        )}
        {step.error && step.status === "failed" && (
          <div className="mt-2 rounded-md bg-destructive/5 p-2 text-sm text-destructive" data-testid={`step-error-${step.id}`}>
            {step.error}
          </div>
        )}
      </div>
    </div>
  );
}

export function WorkflowVisualization({ workflow, currentStepId }: WorkflowVisualizationProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!workflow) {
    return null;
  }

  return (
    <Card className="overflow-hidden" data-testid="card-workflow-visualization">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 gap-4 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/10 to-blue-500/10">
              <Bot className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <CardTitle className="text-lg">{workflow.name}</CardTitle>
              {workflow.description && (
                <p className="text-sm text-muted-foreground">{workflow.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              {workflow.steps.length} step{workflow.steps.length !== 1 ? "s" : ""}
            </Badge>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="button-toggle-workflow">
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
          </div>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-0">
              {workflow.steps.map((step, index) => (
                <StepNode
                  key={step.id}
                  step={step}
                  isActive={step.id === currentStepId}
                  isLast={index === workflow.steps.length - 1}
                  index={index}
                />
              ))}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
