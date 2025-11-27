import { useState, useEffect, useRef } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { CommandInput } from "@/components/agent/CommandInput";
import { ExecutionLog, Step } from "@/components/agent/ExecutionLog";
import { BrowserPreview } from "@/components/agent/BrowserPreview";
import { motion } from "framer-motion";
import generatedImage from "@assets/generated_images/abstract_digital_network_visualization.png";
import { AutomationWebSocket, type WebSocketMessage } from "@/lib/websocket";
import { useToast } from "@/hooks/use-toast";

export default function Dashboard() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [currentUrl, setCurrentUrl] = useState("");
  const wsRef = useRef<AutomationWebSocket | null>(null);
  const { toast } = useToast();
  
  useEffect(() => {
    const ws = new AutomationWebSocket(
      (message: WebSocketMessage) => {
        switch (message.type) {
          case "job_started":
            console.log("Job started:", message.jobId);
            break;
          case "step":
            setSteps((prev) => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1].status = 'completed';
              }
              return [...updated, message.step];
            });
            
            if (message.step.type === 'browsing' && message.step.detail) {
              const urlMatch = message.step.detail.match(/https?:\/\/[^\s]+/);
              if (urlMatch) {
                setCurrentUrl(urlMatch[0]);
              }
            }
            break;
          case "job_completed":
            setIsProcessing(false);
            if (message.success) {
              toast({
                title: "Task Completed",
                description: message.result || "Automation finished successfully",
              });
            } else {
              toast({
                title: "Task Failed",
                description: message.error || "An error occurred",
                variant: "destructive",
              });
            }
            break;
          case "error":
            setIsProcessing(false);
            toast({
              title: "Error",
              description: message.message,
              variant: "destructive",
            });
            break;
        }
      },
      (error) => {
        console.error("WebSocket error:", error);
        toast({
          title: "Connection Error",
          description: "Failed to connect to automation server",
          variant: "destructive",
        });
      }
    );

    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
    };
  }, [toast]);
  
  const handleCommand = async (prompt: string) => {
    if (!wsRef.current?.isConnected()) {
      toast({
        title: "Not Connected",
        description: "Connecting to server...",
      });
      return;
    }

    setIsProcessing(true);
    setSteps([]);
    setCurrentUrl("about:blank");

    wsRef.current.send({
      type: "execute",
      prompt,
    });
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Background Gradient/Texture */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[100px]" />
          <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")` }} />
        </div>

        {/* Header Area */}
        <header className="relative z-10 pt-8 pb-4 px-8">
          <div className="max-w-[1600px] mx-auto w-full">
            <h1 className="text-3xl md:text-4xl font-display font-bold mb-2 tracking-tight">
              Agent <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-cyan-400">Command Center</span>
            </h1>
            <p className="text-muted-foreground text-lg font-light">
              Orchestrate complex web automation workflows with natural language.
            </p>
          </div>
        </header>

        {/* Command Bar */}
        <div className="relative z-20 px-8 mb-6">
          <div className="max-w-[1600px] mx-auto w-full">
            <CommandInput onSubmit={handleCommand} isProcessing={isProcessing} />
          </div>
        </div>

        {/* Work Area */}
        <div className="flex-1 relative z-10 px-8 pb-8 min-h-0">
          <div className="max-w-[1600px] mx-auto w-full h-full grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Col: Execution Log */}
            <div className="lg:col-span-4 h-full min-h-[300px]">
              <ExecutionLog steps={steps} />
            </div>

            {/* Right Col: Preview / Visuals */}
            <div className="lg:col-span-8 h-full flex flex-col gap-6 min-h-[300px]">
              {steps.length > 0 ? (
                <BrowserPreview 
                  url={currentUrl} 
                  isLoading={steps.some(s => s.type === 'browsing' && s.status === 'running')} 
                  content={
                     currentUrl.includes("google") ? (
                       <div className="p-6 space-y-6">
                         <div className="flex gap-4 items-center border-b pb-4 border-gray-200">
                           <div className="w-24 h-8 bg-gray-300 rounded" />
                           <div className="flex-1 h-10 bg-white shadow-sm border rounded-full px-4 flex items-center text-gray-400 text-sm">
                             Search queries...
                           </div>
                         </div>
                         {[1,2,3].map(i => (
                           <div key={i} className="space-y-2">
                             <div className="text-xs text-gray-500">news.source.com › article</div>
                             <div className="text-xl text-blue-700 font-medium hover:underline cursor-pointer">SpaceX Starship Update: Flight 4 Preparations Underway</div>
                             <div className="text-sm text-gray-600 leading-relaxed">
                               SpaceX is preparing for the fourth flight of its Starship megarocket. The company has rolled out the Ship 29 upper stage to the launch pad at Starbase...
                             </div>
                           </div>
                         ))}
                       </div>
                     ) : undefined
                  }
                />
              ) : (
                <div className="h-full w-full rounded-xl overflow-hidden border border-white/10 relative group">
                   <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent z-10" />
                   <img 
                     src={generatedImage} 
                     alt="Agent Visualization" 
                     className="w-full h-full object-cover opacity-50 transition-transform duration-700 group-hover:scale-105"
                   />
                   <div className="absolute bottom-0 left-0 right-0 p-8 z-20">
                     <h3 className="text-2xl font-display font-bold mb-2">Ready for Assignment</h3>
                     <p className="text-muted-foreground max-w-md">
                       Eko is standing by. Enter a prompt to begin automation. The agent can browse, extract data, and generate reports.
                     </p>
                   </div>
                </div>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
