import { Activity, Clock, Chrome } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface StatusBarProps {
  connectionStatus?: "connected" | "disconnected" | "connecting";
  browserVersion?: string;
  executionTime?: string;
}

export function StatusBar({ 
  connectionStatus = "connected", 
  browserVersion = "Chromium 131.0",
  executionTime 
}: StatusBarProps) {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "bg-green-500";
      case "disconnected":
        return "bg-gray-400";
      case "connecting":
        return "bg-yellow-500";
    }
  };

  return (
    <div className="flex items-center justify-between h-8 px-4 border-t border-border bg-muted/30 text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${getStatusColor()}`} data-testid="indicator-connection-status" />
          <span className="capitalize text-muted-foreground">{connectionStatus}</span>
        </div>
        {executionTime && (
          <>
            <div className="h-3 w-px bg-border" />
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-muted-foreground" data-testid="text-execution-time">{executionTime}</span>
            </div>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Chrome className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground" data-testid="text-browser-version">{browserVersion}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground">Playwright MCP</span>
        </div>
      </div>
    </div>
  );
}
