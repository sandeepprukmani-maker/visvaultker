import { FileCode, Play, Edit, Trash2, Copy, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface TaskCardProps {
  id: string;
  name: string;
  description: string;
  language: string;
  lastRun?: string;
  status?: "success" | "failed" | "pending";
  onRun?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
}

export function TaskCard({
  id,
  name,
  description,
  language,
  lastRun,
  status,
  onRun,
  onEdit,
  onDelete,
  onDuplicate,
}: TaskCardProps) {
  return (
    <Card className="hover-elevate" data-testid={`card-task-${id}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
              <FileCode className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h4 className="text-sm font-medium" data-testid={`text-task-name-${id}`}>{name}</h4>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="icon" variant="ghost" data-testid={`button-task-menu-${id}`}>
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onEdit && (
                <DropdownMenuItem onClick={onEdit} data-testid={`button-edit-task-${id}`}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </DropdownMenuItem>
              )}
              {onDuplicate && (
                <DropdownMenuItem onClick={onDuplicate} data-testid={`button-duplicate-task-${id}`}>
                  <Copy className="w-4 h-4 mr-2" />
                  Duplicate
                </DropdownMenuItem>
              )}
              {onDelete && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={onDelete} className="text-destructive" data-testid={`button-delete-task-${id}`}>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <p className="text-xs text-muted-foreground line-clamp-2">{description}</p>
      </CardContent>
      <CardFooter className="pt-0 flex-wrap gap-2">
        <Badge variant="secondary" className="text-xs">
          {language}
        </Badge>
        {status && (
          <Badge 
            variant={status === "success" ? "default" : status === "failed" ? "destructive" : "secondary"}
            className="text-xs"
            data-testid={`badge-status-${id}`}
          >
            {status}
          </Badge>
        )}
        {lastRun && (
          <span className="text-xs text-muted-foreground ml-auto">
            {lastRun}
          </span>
        )}
        {onRun && (
          <Button size="sm" className="ml-auto" onClick={onRun} data-testid={`button-run-task-${id}`}>
            <Play className="w-3 h-3 mr-1" />
            Run
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
