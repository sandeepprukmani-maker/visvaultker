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
      return apiRequest("/api/settings", "PATCH", updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/settings"] });
    },
  });

  // Delete automation mutation
  const deleteAutomationMutation = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest(`/api/automations/${id}`, "DELETE");
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
    updateSettingsMutation.mutate({ selectedModel: model });
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

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      <HistorySidebar
        history={historyItems}
        cache={cacheItems}
        onRerun={handleRerun}
        onDelete={handleDelete}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 flex items-center justify-end px-6 flex-shrink-0 bg-background">
          <div className="flex items-center gap-2">
            <SettingsPanel
              selectedModel={settings?.selectedModel || "openai"}
              onModelChange={handleModelChange}
            />
            <ThemeToggle />
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto">
          <div className={`transition-all duration-300 ${
            hasExecuted ? "pt-8" : "h-full flex items-center justify-center"
          }`}>
            <div className="w-full px-6">

              {/* Search Input */}
              <div className="mb-8">
                <SearchInput
                  onSubmit={handleExecute}
                  isExecuting={isExecuting}
                  centered={!hasExecuted}
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
