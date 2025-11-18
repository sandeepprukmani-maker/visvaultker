import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { SearchInput } from "@/components/search-input";
import { ExecutionResults } from "@/components/execution-results";
import { HistorySidebar } from "@/components/history-sidebar";
import { LiveExecutionIndicator } from "@/components/live-execution-indicator";
import { ThemeToggle } from "@/components/theme-toggle";
import { SettingsPanel } from "@/components/settings-panel";
import { useWebSocket } from "@/lib/websocket";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { Sparkles } from "lucide-react";
import type { Automation, Settings } from "@shared/schema";

export default function Home() {
  const { toast } = useToast();
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<Automation | null>(null);
  const [hasExecuted, setHasExecuted] = useState(false);
  const [liveStatus, setLiveStatus] = useState("");

  // Fetch settings
  const { data: settings } = useQuery<Settings>({
    queryKey: ["/api/settings"],
  });

  // Fetch automations (history)
  const { data: automations = [] } = useQuery<Automation[]>({
    queryKey: ["/api/automations"],
  });

  // Fetch cache
  const { data: cache = [] } = useQuery<any[]>({
    queryKey: ["/api/cache"],
  });

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async (updates: Partial<Settings>) => {
      return apiRequest("PATCH", "/api/settings", updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/settings"] });
    },
  });

  // Delete automation mutation
  const deleteAutomationMutation = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest("DELETE", `/api/automations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/automations"] });
      toast({
        title: "Deleted",
        description: "Automation removed from history",
      });
    },
  });

  // WebSocket for real-time updates
  const { send, isConnected } = useWebSocket({
    onMessage: (message) => {
      switch (message.type) {
        case "execution_started":
          setIsExecuting(true);
          setLiveStatus("Starting automation...");
          break;

        case "execution_log":
          const log = message.data.log;
          setLiveStatus(log.action);
          
          // Update current execution with new log
          setCurrentExecution((prev) => {
            if (!prev) return prev;
            const logs = [...(prev.logs || []), log];
            return { ...prev, logs };
          });
          break;

        case "execution_completed":
          setIsExecuting(false);
          setLiveStatus("");
          
          // Update current execution with final result
          setCurrentExecution((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              status: "success",
              result: message.data.result,
              duration: message.data.duration,
              logs: message.data.logs,
            };
          });

          // Refresh history
          queryClient.invalidateQueries({ queryKey: ["/api/automations"] });

          toast({
            title: "Success",
            description: "Automation completed successfully",
          });
          break;

        case "execution_error":
          setIsExecuting(false);
          setLiveStatus("");
          
          // Update current execution with error
          setCurrentExecution((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              status: "error",
              error: message.data.error,
            };
          });

          // Refresh history
          queryClient.invalidateQueries({ queryKey: ["/api/automations"] });

          toast({
            title: "Error",
            description: message.data.error,
            variant: "destructive",
          });
          break;
      }
    },
  });

  const handleExecute = async (prompt: string) => {
    if (!isConnected) {
      toast({
        title: "Connection Error",
        description: "WebSocket not connected. Please refresh the page.",
        variant: "destructive",
      });
      return;
    }

    if (!settings?.selectedModel) {
      toast({
        title: "Configuration Error",
        description: "Please select an AI model in settings.",
        variant: "destructive",
      });
      return;
    }

    setHasExecuted(true);
    setIsExecuting(true);
    
    // Create initial execution state
    const newExecution: Automation = {
      id: Date.now().toString(),
      prompt,
      status: "running",
      logs: [],
      result: null,
      error: null,
      duration: null,
      model: settings.selectedModel,
      createdAt: new Date(),
    };
    
    setCurrentExecution(newExecution);

    // Send execution request via WebSocket
    send({
      type: "execute_automation",
      prompt,
      model: settings.selectedModel,
    });
  };

  const handleRerun = (id: string) => {
    const item = [...automations, ...cache].find((i) => i.id === id);
    if (item) {
      handleExecute(item.prompt);
    }
  };

  const handleDelete = (id: string) => {
    deleteAutomationMutation.mutate(id);
  };

  const handleModelChange = (model: string) => {
    console.log('Model change called with:', model);
    updateSettingsMutation.mutate({ selectedModel: model });
  };

  const handleAutomationModeChange = (mode: string) => {
    console.log('Automation mode change called with:', mode);
    updateSettingsMutation.mutate({ automationMode: mode });
  };

  const handleScreenshotModeChange = (mode: string) => {
    console.log('Screenshot mode change called with:', mode);
    updateSettingsMutation.mutate({ screenshotMode: mode });
  };

  // Format history items for sidebar
  const historyItems = automations.map((a) => ({
    id: a.id,
    prompt: a.prompt,
    status: a.status,
    createdAt: a.createdAt.toString(),
  }));

  // Format cache items for sidebar
  const cacheItems = cache.map((c) => ({
    id: c.id,
    prompt: c.prompt,
    useCount: c.useCount || "0",
    lastUsed: c.lastUsed?.toString() || new Date().toISOString(),
  }));

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      {isSidebarOpen && (
        <HistorySidebar
          history={historyItems}
          cache={cacheItems}
          onRerun={handleRerun}
          onDelete={handleDelete}
          onClose={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden transition-all duration-300">
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-6 flex-shrink-0 bg-background">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="h-8 w-8 flex items-center justify-center hover-elevate active-elevate-2 rounded-md transition-all"
            data-testid="button-toggle-sidebar"
          >
            <svg 
              preserveAspectRatio="xMidYMin" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="currentColor" 
              aria-hidden="true"
            >
              <path 
                fillRule="evenodd" 
                d="M2 4.8A2.8 2.8 0 0 1 4.8 2h13.9a2.8 2.8 0 0 1 2.8 2.8v13.9a2.8 2.8 0 0 1-2.8 2.8H4.8A2.8 2.8 0 0 1 2 18.7V4.8Zm9.25-.3a1 1 0 0 1 1-1h6.45A1.3 1.3 0 0 1 20 4.8v13.9a1.3 1.3 0 0 1-1.3 1.3h-6.45a1 1 0 0 1-1-1V4.5Zm-1.5 0a1 1 0 0 0-1-1H4.8a1.3 1.3 0 0 0-1.3 1.3v13.9A1.3 1.3 0 0 0 4.8 20h3.95a1 1 0 0 0 1-1V4.5Z" 
                clipRule="evenodd"
              />
              <path d="M4.125 4.85a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <SettingsPanel
              selectedModel={settings?.selectedModel || "openai"}
              onModelChange={handleModelChange}
              automationMode={settings?.automationMode || "act"}
              onAutomationModeChange={handleAutomationModeChange}
              screenshotMode={settings?.screenshotMode || "none"}
              onScreenshotModeChange={handleScreenshotModeChange}
            />
            <ThemeToggle />
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto">
          <div className="pt-32 transition-all duration-300">
            <div className="w-full px-6">

              {/* Title */}
              <div className="mb-6 text-center">
                <h1 className="text-4xl font-bold tracking-tight" data-testid="text-app-title">
                  <span className="bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600 bg-clip-text text-transparent font-extrabold">
                    ZenSmart
                  </span>
                  {" "}
                  <span className="text-foreground font-extrabold">Executor</span>
                </h1>
                <p className="text-sm text-muted-foreground mt-2">
                  Automate the web with AI-powered precision
                </p>
              </div>

              {/* Search Input */}
              <div className="mb-8">
                <SearchInput
                  onSubmit={handleExecute}
                  isExecuting={isExecuting}
                  centered={true}
                />
              </div>

              {/* Results */}
              {currentExecution && (
                <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
                  <ExecutionResults
                    status={currentExecution.status as any}
                    prompt={currentExecution.prompt}
                    logs={currentExecution.logs as any || []}
                    result={currentExecution.result}
                    error={currentExecution.error || undefined}
                    duration={currentExecution.duration || undefined}
                  />
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Live Execution Indicator */}
      {isExecuting && (
        <LiveExecutionIndicator status={liveStatus || "Processing..."} />
      )}
    </div>
  );
}
