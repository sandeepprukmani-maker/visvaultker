import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Edit, GitBranch } from "lucide-react";

interface WorkflowCardProps {
  id: string;
  title: string;
  description: string;
  tasks: string[];
  lastRun?: string;
  runCount: number;
  onRun?: () => void;
  onEdit?: () => void;
}

export function WorkflowCard({
  id,
  title,
  description,
  tasks,
  lastRun,
  runCount,
  onRun,
  onEdit,
}: WorkflowCardProps) {
  return (
    <Card className="hover-elevate" data-testid={`workflow-card-${id}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <GitBranch className="h-4 w-4 text-primary" />
              <CardTitle className="text-lg">{title}</CardTitle>
            </div>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium mb-2">Tasks ({tasks.length})</p>
            <div className="flex flex-wrap gap-2">
              {tasks.slice(0, 3).map((task, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {task}
                </Badge>
              ))}
              {tasks.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{tasks.length - 3} more
                </Badge>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {lastRun && <span>Last run: {lastRun}</span>}
            <span>{runCount} executions</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button size="sm" onClick={onRun} data-testid={`button-run-workflow-${id}`}>
          <Play className="h-3 w-3 mr-1" />
          Run Workflow
        </Button>
        <Button size="sm" variant="outline" onClick={onEdit} data-testid={`button-edit-workflow-${id}`}>
          <Edit className="h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
}
