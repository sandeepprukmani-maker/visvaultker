import { useState, useEffect, useRef } from "react";
import { Switch, Route } from "wouter";
import { queryClient, apiRequest } from "./lib/queryClient";
import { QueryClientProvider, useQuery, useMutation } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeToggle } from "@/components/theme-toggle";
import { ConnectionStatusBadge } from "@/components/connection-status";
import { HistorySidebar } from "@/components/history-sidebar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useIsMobile } from "@/hooks/use-mobile";
import Home from "@/pages/home";
import NotFound from "@/pages/not-found";
import { type AutomationTask, type ConnectionStatus } from "@shared/schema";
import { Bot, History, PanelLeftClose, PanelLeft } from "lucide-react";

function AppContent() {
  const [tasks, setTasks] = useState<AutomationTask[]>([]);
  const [activeTask, setActiveTask] = useState<AutomationTask | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const isMobile = useIsMobile();
  const activeTaskIdRef = useRef<string | null>(null);

  useEffect(() => {
    activeTaskIdRef.current = activeTask?.id || null;
  }, [activeTask?.id]);

  const { data: fetchedTasks } = useQuery<AutomationTask[]>({
    queryKey: ["/api/tasks"],
  });

  useEffect(() => {
    if (fetchedTasks) {
      setTasks(fetchedTasks);
    }
  }, [fetchedTasks]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
      setConnectionStatus("connected");
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "task_update") {
          const updatedTask = data.task as AutomationTask;
          setTasks((prev) => {
            const existing = prev.find((t) => t.id === updatedTask.id);
            if (existing) {
              return prev.map((t) => (t.id === updatedTask.id ? updatedTask : t));
            }
            return [updatedTask, ...prev];
          });
          if (activeTaskIdRef.current === updatedTask.id) {
            setActiveTask(updatedTask);
          }
        } else if (data.type === "connection_status") {
          setConnectionStatus(data.status);
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = () => {
      setConnectionStatus("disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleNewTask = (task: AutomationTask) => {
    setTasks((prev) => [task, ...prev]);
    setActiveTask(task);
  };

  const handleTaskUpdate = (task: AutomationTask) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? task : t))
    );
    if (activeTask?.id === task.id) {
      setActiveTask(task);
    }
  };

  const [chatKey, setChatKey] = useState(0);

  const clearHistoryMutation = useMutation({
    mutationFn: async () => {
      await apiRequest("DELETE", "/api/tasks");
    },
    onSuccess: () => {
      setTasks([]);
      setActiveTask(null);
      setChatKey((prev) => prev + 1);
      queryClient.invalidateQueries({ queryKey: ["/api/tasks"] });
    },
  });

  const handleTaskSelect = (task: AutomationTask) => {
    setActiveTask(task);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleClearHistory = () => {
    clearHistoryMutation.mutate();
  };

  const handleNewChat = () => {
    setActiveTask(null);
    setChatKey((prev) => prev + 1);
  };

  const HistoryPanel = (
    <HistorySidebar
      tasks={tasks}
      activeTaskId={activeTask?.id}
      onTaskSelect={handleTaskSelect}
      onClearHistory={handleClearHistory}
    />
  );

  return (
    <div className="flex h-screen w-full bg-background">
      {!isMobile && sidebarOpen && (
        <div className="w-80 border-r flex-shrink-0">
          {HistoryPanel}
        </div>
      )}

      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between gap-4 h-14 px-4 border-b bg-background sticky top-0 z-50">
          <div className="flex items-center gap-3">
            {!isMobile && (
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                data-testid="button-toggle-sidebar"
              >
                {sidebarOpen ? (
                  <PanelLeftClose className="h-4 w-4" />
                ) : (
                  <PanelLeft className="h-4 w-4" />
                )}
              </Button>
            )}
            
            {isMobile && (
              <Sheet>
                <SheetTrigger asChild>
                  <Button size="icon" variant="ghost" data-testid="button-mobile-history">
                    <History className="h-4 w-4" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0 w-80">
                  {HistoryPanel}
                </SheetContent>
              </Sheet>
            )}
            
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary/10">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <h1 className="text-lg font-semibold hidden sm:block">
                Browser Pilot
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ConnectionStatusBadge status={connectionStatus} />
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewChat}
              data-testid="button-new-chat"
            >
              New Chat
            </Button>
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          <Switch>
            <Route path="/">
              <Home
                key={chatKey}
                onNewTask={handleNewTask}
                onTaskUpdate={handleTaskUpdate}
                activeTask={activeTask}
                connectionStatus={connectionStatus}
              />
            </Route>
            <Route component={NotFound} />
          </Switch>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AppContent />
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
