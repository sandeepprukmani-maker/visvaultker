import { Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RecordingIndicatorProps {
  isRecording: boolean;
  onStop?: () => void;
}

export function RecordingIndicator({ isRecording, onStop }: RecordingIndicatorProps) {
  if (!isRecording) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-md shadow-lg" data-testid="indicator-recording">
      <div className="w-2 h-2 rounded-full bg-destructive-foreground animate-pulse" />
      <span className="text-sm font-medium">Recording...</span>
      {onStop && (
        <Button 
          size="sm" 
          variant="secondary"
          onClick={onStop}
          className="h-7 ml-2"
          data-testid="button-stop-recording"
        >
          <Square className="w-3 h-3 mr-1" />
          Stop
        </Button>
      )}
    </div>
  );
}
