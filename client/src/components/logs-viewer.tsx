import { useEffect, useRef } from "react";
import { clsx } from "clsx";
import type { AutomationLog } from "@shared/schema";
import { format } from "date-fns";
import { motion, AnimatePresence } from "framer-motion";

interface LogsViewerProps {
  logs: AutomationLog[];
  className?: string;
}

export function LogsViewer({ logs, className }: LogsViewerProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className={clsx(
      "bg-black rounded-lg border border-border/50 overflow-hidden flex flex-col font-mono text-sm shadow-inner",
      className
    )}>
      <div className="bg-white/5 px-4 py-2 border-b border-border/50 flex items-center gap-2">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
        </div>
        <span className="text-xs text-muted-foreground ml-2">Console Output</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin min-h-[300px] max-h-[600px]">
        {logs.length === 0 && (
          <div className="text-muted-foreground/40 italic text-center py-8">
            Waiting for logs...
          </div>
        )}
        
        <AnimatePresence initial={false}>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-3 group"
            >
              <span className="text-muted-foreground/30 shrink-0 select-none text-xs pt-1">
                {log.timestamp ? format(new Date(log.timestamp), "HH:mm:ss") : "--:--:--"}
              </span>
              <span className={clsx(
                "break-all",
                log.type === 'error' ? "text-red-400" : 
                log.type === 'action' ? "text-blue-400" : "text-gray-300"
              )}>
                <span className="mr-2 opacity-50 select-none">
                  {log.type === 'action' ? '→' : 
                   log.type === 'error' ? '✖' : '›'}
                </span>
                {log.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={endRef} />
      </div>
    </div>
  );
}
