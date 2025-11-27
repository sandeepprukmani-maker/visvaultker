import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, AlertCircle, FileText, Globe, Search, Cpu, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed';
export type StepType = 'thinking' | 'browsing' | 'extracting' | 'writing' | 'success' | 'error';

export interface Step {
  id: string;
  type: StepType;
  message: string;
  detail?: string;
  timestamp: number;
  status: StepStatus;
}

interface ExecutionLogProps {
  steps: Step[];
}

export function ExecutionLog({ steps }: ExecutionLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps]);

  const getIcon = (type: StepType, status: StepStatus) => {
    if (status === 'running') return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
    if (status === 'failed') return <AlertCircle className="h-4 w-4 text-destructive" />;
    
    switch (type) {
      case 'thinking': return <Cpu className="h-4 w-4 text-purple-400" />;
      case 'browsing': return <Globe className="h-4 w-4 text-blue-400" />;
      case 'extracting': return <Search className="h-4 w-4 text-yellow-400" />;
      case 'writing': return <FileText className="h-4 w-4 text-green-400" />;
      case 'success': return <CheckCircle2 className="h-4 w-4 text-primary" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-destructive" />;
      default: return <ChevronRight className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="h-full flex flex-col bg-black/40 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-white/10 bg-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-muted-foreground">Execution Stream</span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground opacity-50">LIVE</span>
      </div>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
      >
        <AnimatePresence mode="popLayout">
          {steps.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              className="h-full flex flex-col items-center justify-center text-center text-muted-foreground p-8"
            >
              <Cpu className="h-12 w-12 mb-4 opacity-20" />
              <p>Waiting for command...</p>
            </motion.div>
          ) : (
            steps.map((step, index) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={cn(
                  "group relative pl-4 border-l-2 py-1",
                  step.status === 'running' ? "border-primary bg-primary/5" : 
                  step.status === 'completed' ? "border-white/20" : 
                  step.status === 'failed' ? "border-destructive" : "border-white/5"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    {getIcon(step.type, step.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className={cn(
                        "font-medium truncate",
                        step.status === 'running' ? "text-primary" : "text-foreground"
                      )}>
                        {step.message}
                      </span>
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {new Date(step.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                    
                    {step.detail && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="mt-1.5 text-xs text-muted-foreground/80 break-all font-light bg-black/30 p-2 rounded border border-white/5"
                      >
                        {step.detail}
                      </motion.div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
        
        {steps.some(s => s.status === 'running') && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }}
            className="pl-4 border-l-2 border-transparent py-1 flex items-center gap-2 text-xs text-muted-foreground animate-pulse"
          >
            <div className="h-1.5 w-1.5 bg-primary rounded-full" />
            Thinking...
          </motion.div>
        )}
      </div>
    </div>
  );
}
