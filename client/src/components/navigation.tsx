import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";
import { History, Settings, Zap } from "lucide-react";

interface NavigationProps {
  onHistoryClick: () => void;
  onNewClick: () => void;
  onSettingsClick: () => void;
}

export function Navigation({ onHistoryClick, onNewClick, onSettingsClick }: NavigationProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-blue-500">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-semibold tracking-tight">Eko</span>
            <span className="text-xs text-muted-foreground">Web Automation</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={onNewClick}
            data-testid="button-new-automation"
            className="bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600"
          >
            <Zap className="mr-2 h-4 w-4" />
            New Automation
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onHistoryClick}
            data-testid="button-history"
            aria-label="View history"
          >
            <History className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onSettingsClick}
            data-testid="button-settings"
            aria-label="Settings"
          >
            <Settings className="h-5 w-5" />
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
