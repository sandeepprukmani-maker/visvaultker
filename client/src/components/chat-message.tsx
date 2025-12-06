import { type Message, type BrowserAction } from "@shared/schema";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  MousePointer2,
  Type,
  Eye,
  Navigation,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Terminal,
} from "lucide-react";

interface ChatMessageProps {
  message: Message;
}

function getActionIcon(type: string) {
  switch (type.toLowerCase()) {
    case "click":
    case "playwright_click":
      return <MousePointer2 className="h-3.5 w-3.5" />;
    case "fill":
    case "type":
    case "playwright_fill":
      return <Type className="h-3.5 w-3.5" />;
    case "navigate":
    case "playwright_navigate":
      return <Navigation className="h-3.5 w-3.5" />;
    case "screenshot":
    case "playwright_screenshot":
      return <Eye className="h-3.5 w-3.5" />;
    default:
      return <Terminal className="h-3.5 w-3.5" />;
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case "success":
      return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />;
    case "error":
      return <XCircle className="h-3.5 w-3.5 text-destructive" />;
    case "running":
      return <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />;
    default:
      return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
  }
}

function ActionCard({ action }: { action: BrowserAction }) {
  return (
    <div
      className="flex items-center gap-3 py-2 px-3 rounded-md bg-muted/50"
      data-testid={`action-item-${action.id}`}
    >
      <div className="flex items-center justify-center w-7 h-7 rounded-md bg-background">
        {getActionIcon(action.type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">
            {action.type.replace("playwright_", "")}
          </span>
          {action.target && (
            <code className="text-xs font-mono text-muted-foreground truncate max-w-48">
              {action.target}
            </code>
          )}
        </div>
        {action.value && (
          <p className="text-xs text-muted-foreground truncate">
            Value: {action.value}
          </p>
        )}
        {action.error && (
          <p className="text-xs text-destructive truncate">{action.error}</p>
        )}
      </div>
      <div className="flex-shrink-0">{getStatusIcon(action.status)}</div>
    </div>
  );
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isSystem) {
    return (
      <div
        className="flex justify-center py-2"
        data-testid={`message-system-${message.id}`}
      >
        <Badge variant="secondary" className="font-normal text-xs">
          {message.content}
        </Badge>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex gap-3 max-w-4xl",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
      data-testid={`message-${message.role}-${message.id}`}
    >
      <div
        className={cn(
          "flex flex-col gap-1",
          isUser ? "items-end" : "items-start"
        )}
      >
        <Card
          className={cn(
            "px-4 py-3 max-w-lg",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card"
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </Card>

        {message.actions && message.actions.length > 0 && (
          <Card className="w-full max-w-lg mt-2 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Browser Actions
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {message.actions.map((action) => (
                <ActionCard key={action.id} action={action} />
              ))}
            </div>
          </Card>
        )}

        <span className="text-xs text-muted-foreground px-1">{timestamp}</span>
      </div>
    </div>
  );
}
