import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Navigation } from "@/components/navigation";
import { PromptInput } from "@/components/prompt-input";
import { TemplateCards } from "@/components/template-cards";
import { WorkflowVisualization } from "@/components/workflow-visualization";
import { ExecutionStatus } from "@/components/execution-status";
import { HistoryDrawer } from "@/components/history-drawer";
import { SettingsDialog } from "@/components/settings-dialog";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import type { Execution, Workflow, LogEntry, ExecutionStatus as ExecStatus } from "@shared/schema";
import { Settings, RotateCcw } from "lucide-react";

type AppState = "idle" | "input" | "planning" | "executing" | "completed" | "failed";

export default function Home() {
  const { toast } = useToast();
  const [appState, setAppState] = useState<AppState>("idle");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<Execution | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [progress, setProgress] = useState(0);
  const promptInputRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: executions = [], isLoading: isLoadingHistory } = useQuery<Execution[]>({
    queryKey: ["/api/executions"],
  });

  const generateMutation = useMutation({
    mutationFn: async (prompt: string) => {
      const response = await apiRequest("POST", "/api/workflow/generate", { prompt });
      return response.json();
    },
    onSuccess: (data: { execution: Execution; workflow: Workflow }) => {
      setCurrentExecution(data.execution);
      setWorkflow(data.workflow);
      setAppState("planning");
      addLog("info", "Workflow generated successfully");
      queryClient.invalidateQueries({ queryKey: ["/api/executions"] });
      
      executeMutation.mutate(data.execution.id);
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to generate workflow",
        description: error.message,
        variant: "destructive",
      });
      setAppState("input");
    },
  });

  const executeMutation = useMutation({
    mutationFn: async (executionId: string) => {
      const response = await apiRequest("POST", "/api/workflow/execute", { executionId });
      return response.json();
    },
    onSuccess: (data: { success: boolean; execution: Execution }) => {
      setCurrentExecution(data.execution);
      setAppState("executing");
      addLog("info", "Execution started");
      startPolling();
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to start execution",
        description: error.message,
        variant: "destructive",
      });
      setAppState("failed");
    },
  });

  const controlMutation = useMutation({
    mutationFn: async ({ executionId, action }: { executionId: string; action: "pause" | "resume" | "cancel" }) => {
      const response = await apiRequest("POST", "/api/workflow/control", { executionId, action });
      return response.json();
    },
    onSuccess: (data: { success: boolean; execution: Execution }, variables) => {
      setCurrentExecution(data.execution);
      if (variables.action === "pause") {
        addLog("warning", "Execution paused");
      } else if (variables.action === "resume") {
        addLog("info", "Execution resumed");
      } else if (variables.action === "cancel") {
        addLog("warning", "Execution cancelled");
        setAppState("failed");
        stopPolling();
      }
      queryClient.invalidateQueries({ queryKey: ["/api/executions"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to control execution",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const addLog = useCallback((level: LogEntry["level"], message: string, stepId?: string) => {
    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    setLogs((prev) => [...prev, { timestamp, level, message, stepId }]);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollingRef.current) return;
    
    const poll = async () => {
      if (!currentExecution?.id) return;
      
      try {
        const response = await fetch(`/api/executions/${currentExecution.id}`);
        if (!response.ok) return;
        
        const data = await response.json();
        const execution = data.execution as Execution;
        
        setCurrentExecution(execution);
        setProgress(execution.progress || 0);
        
        if (data.workflow) {
          setWorkflow(data.workflow as Workflow);
        }
        
        if (execution.logs && Array.isArray(execution.logs)) {
          setLogs(execution.logs as LogEntry[]);
        }
        
        if (execution.status === "completed") {
          setAppState("completed");
          stopPolling();
          queryClient.invalidateQueries({ queryKey: ["/api/executions"] });
        } else if (execution.status === "failed") {
          setAppState("failed");
          stopPolling();
          queryClient.invalidateQueries({ queryKey: ["/api/executions"] });
        } else if (execution.status === "cancelled") {
          setAppState("failed");
          stopPolling();
          queryClient.invalidateQueries({ queryKey: ["/api/executions"] });
        } else if (execution.status === "paused") {
          setAppState("executing");
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    };

    poll();
    pollingRef.current = setInterval(poll, 1000);
  }, [currentExecution?.id, stopPolling]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  useEffect(() => {
    if (currentExecution?.id && (appState === "executing" || appState === "planning")) {
      startPolling();
    }
  }, [currentExecution?.id, appState, startPolling]);

  const handleSubmitPrompt = (prompt: string) => {
    setLogs([]);
    setProgress(0);
    setWorkflow(null);
    addLog("info", `Starting automation: "${prompt}"`);
    generateMutation.mutate(prompt);
  };

  const handleSelectTemplate = (prompt: string) => {
    setAppState("input");
    setTimeout(() => {
      promptInputRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  const handleNewAutomation = () => {
    setAppState("input");
    setCurrentExecution(null);
    setWorkflow(null);
    setLogs([]);
    setProgress(0);
    stopPolling();
  };

  const handleSelectExecution = (execution: Execution) => {
    setCurrentExecution(execution);
    setWorkflow(execution.workflow as Workflow | null);
    setLogs((execution.logs as LogEntry[]) || []);
    setProgress(execution.progress || 0);
    setHistoryOpen(false);
    
    if (execution.status === "completed") {
      setAppState("completed");
    } else if (execution.status === "failed" || execution.status === "cancelled") {
      setAppState("failed");
    } else if (execution.status === "running" || execution.status === "paused") {
      setAppState("executing");
      startPolling();
    } else {
      setAppState("input");
    }
  };

  const handlePause = () => {
    if (currentExecution?.id) {
      controlMutation.mutate({ executionId: currentExecution.id, action: "pause" });
    }
  };

  const handleResume = () => {
    if (currentExecution?.id) {
      controlMutation.mutate({ executionId: currentExecution.id, action: "resume" });
    }
  };

  const handleCancel = () => {
    if (currentExecution?.id) {
      controlMutation.mutate({ executionId: currentExecution.id, action: "cancel" });
    }
  };

  const showInput = appState === "idle" || appState === "input";
  const showExecution = appState === "planning" || appState === "executing" || appState === "completed" || appState === "failed";

  return (
    <div className="min-h-screen bg-background" data-testid="page-home">
      <Navigation
        onHistoryClick={() => setHistoryOpen(true)}
        onNewClick={handleNewAutomation}
        onSettingsClick={() => setSettingsOpen(true)}
      />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-8">
          {appState === "idle" && (
            <EmptyState onGetStarted={() => setAppState("input")} />
          )}

          {showInput && appState !== "idle" && (
            <div ref={promptInputRef}>
              <PromptInput
                onSubmit={handleSubmitPrompt}
                isLoading={generateMutation.isPending}
                disabled={appState !== "input"}
              />
            </div>
          )}

          {showInput && appState === "input" && (
            <TemplateCards onSelectTemplate={handleSelectTemplate} />
          )}

          {showExecution && (
            <div className="space-y-6" data-testid="section-execution">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold" data-testid="text-execution-title">
                    {appState === "completed" 
                      ? "Execution Complete" 
                      : appState === "failed" 
                      ? "Execution Failed" 
                      : "Executing Workflow"}
                  </h2>
                  {currentExecution && (
                    <p className="text-sm text-muted-foreground mt-1" data-testid="text-execution-prompt">
                      {currentExecution.prompt}
                    </p>
                  )}
                </div>
                {(appState === "completed" || appState === "failed") && (
                  <Button
                    variant="outline"
                    onClick={handleNewAutomation}
                    data-testid="button-new-after-complete"
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    New Automation
                  </Button>
                )}
              </div>

              <WorkflowVisualization
                workflow={workflow}
                currentStepId={currentExecution?.currentStep || undefined}
              />

              <ExecutionStatus
                status={(currentExecution?.status as ExecStatus) || "planning"}
                progress={progress}
                currentStep={currentExecution?.currentStep || undefined}
                logs={logs}
                onPause={handlePause}
                onResume={handleResume}
                onCancel={handleCancel}
                isControlling={controlMutation.isPending}
              />
            </div>
          )}
        </div>
      </main>

      <HistoryDrawer
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        executions={executions}
        onSelectExecution={handleSelectExecution}
        isLoading={isLoadingHistory}
      />

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />

      <Button
        variant="ghost"
        size="icon"
        className="fixed bottom-4 right-4 h-10 w-10 rounded-full shadow-lg bg-card border"
        onClick={() => setSettingsOpen(true)}
        data-testid="button-settings-fab"
      >
        <Settings className="h-5 w-5" />
      </Button>
    </div>
  );
}
