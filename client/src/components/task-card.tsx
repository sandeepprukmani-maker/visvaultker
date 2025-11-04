import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Edit, Trash2, Clock } from "lucide-react";

interface TaskCardProps {
  id: string;
  title: string;
  description: string;
  website: string;
  lastRun?: string;
  runCount: number;
  status: "active" | "draft" | "disabled";
  onRun?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function TaskCard({
  id,
  title,
  description,
  website,
  lastRun,
  runCount,
  status,
  onRun,
  onEdit,
  onDelete,
}: TaskCardProps) {
  const statusColors = {
    active: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    draft: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20",
    disabled: "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20",
  };

  return (
    <Card className="hover-elevate" data-testid={`task-card-${id}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription className="mt-1">{description}</CardDescription>
          </div>
          <Badge className={statusColors[status]} variant="outline">
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Website:</span>
            <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono">{website}</code>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {lastRun && (
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{lastRun}</span>
              </div>
            )}
            <span>{runCount} runs</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button size="sm" onClick={onRun} data-testid={`button-run-${id}`}>
          <Play className="h-3 w-3 mr-1" />
          Run
        </Button>
        <Button size="sm" variant="outline" onClick={onEdit} data-testid={`button-edit-${id}`}>
          <Edit className="h-3 w-3" />
        </Button>
        <Button size="sm" variant="outline" onClick={onDelete} data-testid={`button-delete-${id}`}>
          <Trash2 className="h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
}
