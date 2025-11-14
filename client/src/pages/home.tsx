import { useState, useCallback } from "react";
import { PlayCircle, Clock, ChartBar, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PromptInput } from "@/components/PromptInput";
import { StatusIndicator } from "@/components/StatusIndicator";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { HistoryModal } from "@/components/HistoryModal";
import { TokenMetrics } from "@/components/TokenMetrics";
import { TemplateSelector } from "@/components/TemplateSelector";
import { useWebSocket } from "@/hooks/useWebSocket";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import type { WebSocketMessage } from "@shared/schema";

export default function Home() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    result: string;
    executedCode: string;
    pageState: string;
    tokensUsed: number;
    executionTime: number;
  } | null>(null);
  const { toast } = useToast();

  // Handle WebSocket messages for real-time updates
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case "automation_start":
        setIsExecuting(true);
        setShowResults(false);
        setCurrentStep("Initializing automation...");
        break;

      case "automation_progress":
        setCurrentStep(message.data.step);
        break;

      case "automation_complete":
        setExecutionResult({
          result: message.data.result,
          executedCode: message.data.executedCode,
          pageState: message.data.pageState,
          tokensUsed: message.data.tokensUsed,
          executionTime: message.data.executionTime,
        });
        setIsExecuting(false);
        setShowResults(true);
        toast({
          title: "Automation Complete",
          description: "Your automation finished successfully!",
        });
        break;

      case "automation_error":
        setIsExecuting(false);
        toast({
          title: "Automation Failed",
          description: message.data.error,
          variant: "destructive",
        });
        break;
    }
  }, [toast]);

  useWebSocket(handleWebSocketMessage);

  const handleExecute = async (prompt: string) => {
    try {
      setIsExecuting(true);
      setShowResults(false);
      setCurrentStep("Sending request...");

      await apiRequest("POST", "/api/execute", { prompt });
      
      // WebSocket will handle the rest of the updates
    } catch (error) {
      setIsExecuting(false);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to execute automation",
        variant: "destructive",
      });
    }
  };

  const handleNewAutomation = () => {
    setShowResults(false);
    setExecutionResult(null);
    setCurrentStep("");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Status Indicator - Fixed top-right during execution */}
      {isExecuting && (
        <StatusIndicator currentStep={currentStep} />
      )}

      {/* Header - Only visible when showing results/metrics */}
      {(showResults || showMetrics) && (
        <header className="sticky top-0 z-50 h-16 px-8 bg-background/80 backdrop-blur-md border-b flex items-center justify-between">
          <h1 className="text-xl font-semibold" data-testid="text-brand">ZenSmart Executor</h1>
          <nav className="flex items-center gap-6">
            <Button 
              variant="ghost" 
              onClick={handleNewAutomation}
              data-testid="button-new-automation"
            >
              New Automation
            </Button>
            <Button 
              variant="ghost"
              onClick={() => setShowHistory(true)}
              data-testid="button-show-history"
            >
              <Clock className="w-4 h-4 mr-2" />
              History
            </Button>
            <Button 
              variant="ghost"
              onClick={() => setShowMetrics(!showMetrics)}
              data-testid="button-show-metrics"
            >
              <ChartBar className="w-4 h-4 mr-2" />
              Metrics
            </Button>
          </nav>
        </header>
      )}

      {/* Main Content */}
      <main>
        {/* Homepage Hero - Google-style minimal */}
        {!showResults && !showMetrics && (
          <div className="min-h-screen flex items-center justify-center px-4">
            <div className="w-full max-w-2xl mx-auto">
              {/* Logo & Branding */}
              <div className="text-center mb-12">
                <h1 className="text-2xl font-semibold text-foreground mb-3" data-testid="text-logo">
                  ZenSmart Executor
                </h1>
                <p className="text-base text-muted-foreground" data-testid="text-tagline">
                  Automate any website through natural language
                </p>
              </div>

              {/* Template Selector - appears above input when focused */}
              <TemplateSelector onSelectTemplate={(prompt) => handleExecute(prompt)} />

              {/* Main Prompt Input */}
              <PromptInput 
                onExecute={handleExecute}
                disabled={isExecuting}
              />

              {/* Hint text */}
              <p className="text-xs text-muted-foreground text-center mt-4" data-testid="text-hint">
                Press Enter or click Execute to start automation
              </p>

              {/* Quick action buttons */}
              <div className="flex items-center justify-center gap-4 mt-8">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowHistory(true)}
                  data-testid="button-history-hero"
                >
                  <Clock className="w-4 h-4 mr-2" />
                  History
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowMetrics(true)}
                  data-testid="button-metrics-hero"
                >
                  <ChartBar className="w-4 h-4 mr-2" />
                  Metrics
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Results Display - appears below hero */}
        {showResults && executionResult && (
          <div className="max-w-4xl mx-auto px-4 py-12">
            <ResultsDisplay
              result={executionResult.result}
              executedCode={executionResult.executedCode}
              pageState={executionResult.pageState}
              tokensUsed={executionResult.tokensUsed}
              executionTime={executionResult.executionTime}
              onNewAutomation={handleNewAutomation}
              onSaveToHistory={() => {
                toast({
                  description: "Automation already saved to history",
                });
              }}
            />
          </div>
        )}

        {/* Token Metrics Dashboard */}
        {showMetrics && !showResults && (
          <div className="max-w-6xl mx-auto px-4 py-12">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-lg font-medium" data-testid="text-metrics-title">Performance Metrics</h2>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => setShowMetrics(false)}
                data-testid="button-close-metrics"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            <TokenMetrics />
          </div>
        )}
      </main>

      {/* History Modal - Slides in from right */}
      <HistoryModal 
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onReplay={(prompt) => {
          setShowHistory(false);
          handleExecute(prompt);
        }}
      />
    </div>
  );
}
