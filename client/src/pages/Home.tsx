import { useState } from "react";
import Header from "@/components/Header";
import UnifiedAutomationInput from "@/components/UnifiedAutomationInput";
import ExecutionLog from "@/components/ExecutionLog";
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
  }>({});
  const [detectedUrl, setDetectedUrl] = useState<string>("");
  const [usedModes, setUsedModes] = useState<string[]>([]);
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
    <div className="flex min-h-screen flex-col bg-background">
      <Header sessionId={sessionId} status={status} isConnected={isConnected} />
      
      <main className="flex flex-1 overflow-hidden">
        {/* Left Panel - Input Controls */}
        <div className="w-[400px] border-r bg-card/30 p-6 overflow-auto">
          <UnifiedAutomationInput
            onExecute={handleExecute}
            isExecuting={status === "running"}
          />
        </div>

        {/* Right Panel - Execution Log */}
        <div className="flex flex-1 p-4">
          <ExecutionLog 
            entries={logEntries}
            detectedUrl={detectedUrl}
            usedModes={usedModes}
          />
        </div>
      </main>
    </div>
  );
}
