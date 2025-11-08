import { Play, Square, Circle, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useTheme } from "next-themes";

interface TopToolbarProps {
  isRunning?: boolean;
  isRecording?: boolean;
  onRun?: () => void;
  onStop?: () => void;
  onRecord?: () => void;
}

export function TopToolbar({ isRunning, isRecording, onRun, onStop, onRecord }: TopToolbarProps) {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center justify-between h-14 px-4 border-b border-border bg-background">
      <div className="flex items-center gap-2">
        <SidebarTrigger data-testid="button-sidebar-toggle" />
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-1">
          {isRunning ? (
            <Button 
              size="sm" 
              variant="destructive"
              onClick={onStop}
              data-testid="button-stop-execution"
            >
              <Square className="w-3 h-3 mr-1" />
              Stop
            </Button>
          ) : (
            <Button 
              size="sm" 
              variant="default"
              onClick={onRun}
              data-testid="button-run-execution"
            >
              <Play className="w-3 h-3 mr-1" />
              Run
            </Button>
          )}
          <Button 
            size="sm" 
            variant={isRecording ? "destructive" : "secondary"}
            onClick={onRecord}
            data-testid="button-toggle-recording"
          >
            <Circle className={`w-3 h-3 mr-1 ${isRecording ? 'fill-current' : ''}`} />
            {isRecording ? 'Recording' : 'Record'}
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="icon"
          variant="ghost"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          data-testid="button-theme-toggle"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
    </div>
  );
}
