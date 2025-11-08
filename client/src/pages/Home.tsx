import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Header from "@/components/Header";
import AutomationInput from "@/components/AutomationInput";
import BrowserPreview from "@/components/BrowserPreview";
import ExecutionLog, { LogEntry } from "@/components/ExecutionLog";
import CodeOutput from "@/components/CodeOutput";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import type { AutomationRequest, AutomationResponse } from "@shared/schema";

export default function Home() {
  const [status, setStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [generatedCode, setGeneratedCode] = useState<{
    typescript?: string;
    cached?: string;
    agent?: string;
  }>({});
  const [currentUrl, setCurrentUrl] = useState<string>("");
  const { toast } = useToast();

  const automationMutation = useMutation({
    mutationFn: async (data: AutomationRequest) => {
      const response = await fetch("/api/automate", {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          "Content-Type": "application/json",
        },
      });

      const responseData = await response.json();
      
      if (!response.ok) {
        // Capture structured error response
        throw {
          message: responseData.error || "Automation failed",
          response: responseData,
        };
      }
      
      return responseData as AutomationResponse;
    },
    onSuccess: (data) => {
      setStatus("completed");
      setSessionId(data.sessionId);
      setLogEntries(data.logs);
      setGeneratedCode(data.generatedCode);
      
      toast({
        title: "Automation completed",
        description: "Your automation has been executed successfully",
      });
    },
    onError: (error: any) => {
      setStatus("error");
      
      // Populate logs and session ID from error response if available
      if (error.response) {
        if (error.response.logs) {
          setLogEntries(error.response.logs);
        }
        if (error.response.sessionId) {
          setSessionId(error.response.sessionId);
        }
      }
      
      toast({
        title: "Automation failed",
        description: error.message || "An error occurred during automation",
        variant: "destructive",
      });
    },
  });

  const handleExecute = (data: {
    url: string;
    prompt: string;
    mode: "act" | "observe" | "extract" | "agent";
    model?: string;
  }) => {
    setStatus("running");
    setCurrentUrl(data.url);
    setLogEntries([]);
    setGeneratedCode({});
    
    automationMutation.mutate({
      url: data.url,
      prompt: data.prompt,
      mode: data.mode,
      model: data.model || "google/gemini-2.5-flash",
    });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header sessionId={sessionId} status={status} />
      
      <main className="flex flex-1 overflow-hidden">
        {/* Left Panel - Input Controls */}
        <div className="w-[400px] border-r bg-card/30 p-6 overflow-auto">
          <AutomationInput
            onExecute={handleExecute}
            isExecuting={status === "running"}
          />
        </div>

        {/* Right Panel - Preview and Output */}
        <div className="flex flex-1 flex-col">
          {/* Browser Preview - 60% height */}
          <div className="h-[60%] border-b p-4">
            <BrowserPreview
              isLoading={status === "running"}
              currentUrl={currentUrl}
            />
          </div>

          {/* Bottom Section - Log and Code */}
          <div className="flex h-[40%]">
            {/* Execution Log - 50% width */}
            <div className="w-1/2 border-r p-4">
              <ExecutionLog entries={logEntries} />
            </div>

            {/* Code Output - 50% width */}
            <div className="w-1/2 p-4">
              <CodeOutput
                typescriptCode={generatedCode.typescript}
                cachedCode={generatedCode.cached}
                agentCode={generatedCode.agent}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
