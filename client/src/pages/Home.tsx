import { useState } from "react";
import UnifiedAutomationInput from "@/components/UnifiedAutomationInput";
import ExecutionLog from "@/components/ExecutionLog";
import ScreenshotDisplay from "@/components/ScreenshotDisplay";
import { useToast } from "@/hooks/use-toast";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { LogEntry, AutomationResponse } from "@shared/schema";

export default function Home() {
  const [status, setStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [generatedCode, setGeneratedCode] = useState<{
    typescript?: string;
    cached?: string;
    agent?: string;
    locators?: string;
  }>({});
  const [detectedUrl, setDetectedUrl] = useState<string>("");
  const [usedModes, setUsedModes] = useState<string[]>([]);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const { toast } = useToast();

  // WebSocket handlers
  const { isConnected, subscribe } = useWebSocket({
    onLog: (log) => {
      setLogEntries((prev) => [...prev, log]);
    },
    onComplete: (response: AutomationResponse) => {
      setStatus("completed");
      setGeneratedCode(response.generatedCode);
      if (response.detectedUrl) setDetectedUrl(response.detectedUrl);
      if (response.usedModes) setUsedModes(response.usedModes);
      if (response.screenshot) setScreenshots([response.screenshot]);
      
      toast({
        title: "Automation completed",
        description: "Your automation has been executed successfully",
      });
    },
    onError: (error) => {
      setStatus("error");
      toast({
        title: "Automation failed",
        description: error,
        variant: "destructive",
      });
    },
  });

  const handleExecute = async (data: { prompt: string; model: string }) => {
    setStatus("running");
    setLogEntries([]);
    setGeneratedCode({});
    setDetectedUrl("");
    setUsedModes([]);
    setScreenshots([]);

    try {
      const response = await fetch("/api/automate-unified", {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          "Content-Type": "application/json",
        },
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.error || "Automation failed");
      }

      // Subscribe to WebSocket for live updates
      const newSessionId = responseData.sessionId;
      setSessionId(newSessionId);
      subscribe(newSessionId);
    } catch (error) {
      setStatus("error");
      toast({
        title: "Failed to start automation",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">
      <main className="flex flex-1 flex-col items-center justify-start p-6">
        {/* Logo/Title */}
        <div className="mt-24 mb-8 text-center">
          <h1 className="text-5xl font-light tracking-tight">VisionVault</h1>
        </div>

        {/* Input Section */}
        <div className="w-full max-w-2xl mx-auto">
          <UnifiedAutomationInput
            onExecute={handleExecute}
            isExecuting={status === "running"}
          />
        </div>

        {/* Results Section - Execution Log and Screenshot side by side */}
        {(logEntries.length > 0 || status === "running") && (
          <div className="mt-8 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-4">
            <ExecutionLog 
              entries={logEntries}
              detectedUrl={detectedUrl}
              usedModes={usedModes}
            />
            <ScreenshotDisplay screenshots={screenshots} />
          </div>
        )}

        {/* Generated Code Section - locator-based code only */}
        {status === "completed" && generatedCode.locators && (
          <div className="mt-6 w-full max-w-6xl">
            <div className="bg-card border rounded-md p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">Generated Code</h3>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(generatedCode.locators || '');
                    toast({
                      title: "Copied to clipboard",
                      description: "Code copied successfully",
                    });
                  }}
                  className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover-elevate active-elevate-2"
                  data-testid="button-copy-script"
                >
                  Copy Code
                </button>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Rerunnable code using locators and deepLocators (no LLM calls needed)
              </p>
              <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm font-mono max-h-96 overflow-y-auto">
                <code data-testid="text-generated-script">
                  {generatedCode.locators}
                </code>
              </pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
