import { Loader2, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface LiveExecutionIndicatorProps {
  status: string;
  onClose?: () => void;
}

export function LiveExecutionIndicator({ status, onClose }: LiveExecutionIndicatorProps) {
  return (
    <Card className="fixed bottom-6 right-6 p-4 shadow-xl animate-in slide-in-from-bottom-2 fade-in-0 duration-200 min-w-64 max-w-sm" data-testid="indicator-live-execution">
      <div className="flex items-center gap-3">
        <div className="relative">
          <Loader2 className="h-5 w-5 text-primary animate-spin" />
          <div className="absolute inset-0 h-5 w-5 rounded-full bg-primary/20 animate-ping" />
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">Executing automation</p>
          <p className="text-xs text-muted-foreground truncate">{status}</p>
        </div>
        
        {onClose && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={onClose}
            data-testid="button-close-indicator"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </Card>
  );
}
