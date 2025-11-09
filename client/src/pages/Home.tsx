import { useState } from "react";
import { Link } from "wouter";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import ThemeToggle from "@/components/ThemeToggle";
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
    <div className="flex min-h-screen flex-col bg-background">
      {/* Settings and Theme Toggle - Top Right */}
      <div className="absolute top-6 right-6 flex items-center gap-2">
        <ThemeToggle />
        <Link href="/settings">
          <Button variant="ghost" size="icon" data-testid="button-settings">
            <Settings className="h-5 w-5" />
          </Button>
        </Link>
      </div>

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
      </main>
    </div>
  );
}
