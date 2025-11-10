import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Code2, Moon, Sun, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "wouter";

interface HeaderProps {
  sessionId?: string;
  status?: "idle" | "running" | "completed" | "error";
  isConnected?: boolean;
}

export default function Header({ sessionId, status = "idle", isConnected = false }: HeaderProps) {
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
          <h1 className="text-lg font-semibold">VisionVault</h1>
          <p className="text-xs text-muted-foreground">AI Powered</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {isConnected && (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-muted-foreground">Live</span>
          </div>
        )}
        {sessionId && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Session:</span>
            <code className="rounded bg-muted px-2 py-1 font-mono text-xs">{sessionId}</code>
          </div>
        )}
        <Badge variant="outline" className={statusConfig[status].className} data-testid={`status-${status}`}>
          {statusConfig[status].label}
        </Badge>
        <Link href="/settings">
          <Button variant="ghost" size="icon" data-testid="button-settings">
            <Settings className="h-5 w-5" />
          </Button>
        </Link>
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
