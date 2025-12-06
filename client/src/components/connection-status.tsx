import { type ConnectionStatus } from "@shared/schema";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ConnectionStatusProps {
  status: ConnectionStatus;
}

export function ConnectionStatusBadge({ status }: ConnectionStatusProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1.5 font-normal",
        status === "connected" && "border-emerald-500/50 text-emerald-600 dark:text-emerald-400",
        status === "disconnected" && "border-destructive/50 text-destructive",
        status === "connecting" && "border-amber-500/50 text-amber-600 dark:text-amber-400"
      )}
      data-testid="badge-connection-status"
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "connected" && "bg-emerald-500",
          status === "disconnected" && "bg-destructive",
          status === "connecting" && "bg-amber-500 animate-pulse"
        )}
      />
      {status === "connected" && "Connected"}
      {status === "disconnected" && "Disconnected"}
      {status === "connecting" && "Connecting..."}
    </Badge>
  );
}
