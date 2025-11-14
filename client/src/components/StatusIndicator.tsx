import { Loader2 } from "lucide-react";

interface StatusIndicatorProps {
  currentStep: string;
}

export function StatusIndicator({ currentStep }: StatusIndicatorProps) {
  return (
    <div 
      className="fixed top-4 right-4 z-50 p-4 bg-card border rounded-lg shadow-lg flex items-start gap-3 max-w-sm"
      data-testid="status-indicator"
    >
      <Loader2 className="w-4 h-4 animate-spin text-primary flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground" data-testid="text-status">
          Automating...
        </p>
        <p className="text-xs text-muted-foreground mt-1 break-words" data-testid="text-current-step">
          {currentStep}
        </p>
      </div>
    </div>
  );
}
