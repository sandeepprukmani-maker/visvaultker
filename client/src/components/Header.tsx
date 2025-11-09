import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Code2, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

interface HeaderProps {
  sessionId?: string;
  status?: "idle" | "running" | "completed" | "error";
}

export default function Header({ sessionId, status = "idle" }: HeaderProps) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark");
  };

  const statusConfig = {
    idle: { label: "Idle", className: "bg-muted text-muted-foreground border-muted-foreground/20" },
    running: { label: "Running", className: "bg-primary/10 text-primary border-primary/20" },
    completed: { label: "Completed", className: "bg-green-500/10 text-green-500 border-green-500/20" },
    error: { label: "Error", className: "bg-destructive/10 text-destructive border-destructive/20" },
  };

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background px-6">
      <div className="flex items-center gap-3">
        <Code2 className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-lg font-semibold">Stagehand Studio</h1>
          <p className="text-xs text-muted-foreground">Browser Automation Code Generator</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {sessionId && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Session:</span>
            <code className="rounded bg-muted px-2 py-1 font-mono text-xs">{sessionId}</code>
          </div>
        )}
        <Badge variant="outline" className={statusConfig[status].className} data-testid={`status-${status}`}>
          {statusConfig[status].label}
        </Badge>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          data-testid="button-theme-toggle"
        >
          {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </Button>
      </div>
    </header>
  );
}
