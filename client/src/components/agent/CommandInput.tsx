import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ArrowRight, Command, Mic } from "lucide-react";
import { cn } from "@/lib/utils";

interface CommandInputProps {
  onSubmit: (prompt: string) => void;
  isProcessing: boolean;
}

export function CommandInput({ onSubmit, isProcessing }: CommandInputProps) {
  const [prompt, setPrompt] = useState("");
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isProcessing) {
      onSubmit(prompt);
      setPrompt("");
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto relative z-10">
      <form onSubmit={handleSubmit} className="relative group">
        <motion.div
          animate={{
            boxShadow: focused 
              ? "0 0 30px -5px var(--color-primary)" 
              : "0 0 0px 0px transparent",
            borderColor: focused
              ? "var(--color-primary)"
              : "rgba(255,255,255,0.1)"
          }}
          className={cn(
            "bg-black/40 backdrop-blur-xl border rounded-2xl overflow-hidden transition-colors duration-300",
            isProcessing && "opacity-50 cursor-not-allowed"
          )}
        >
          <div className="flex items-center px-6 py-4 gap-4">
            <div className={cn(
              "h-10 w-10 rounded-full flex items-center justify-center transition-colors duration-300",
              focused ? "bg-primary/20 text-primary" : "bg-white/5 text-muted-foreground"
            )}>
              <Sparkles className="h-5 w-5" />
            </div>
            
            <input
              ref={inputRef}
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              disabled={isProcessing}
              placeholder="Describe a task for the agent (e.g., 'Find the latest news on SpaceX and summarize it')"
              className="flex-1 bg-transparent border-none outline-none text-lg placeholder:text-muted-foreground/50 font-light"
            />

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="p-2 hover:bg-white/10 rounded-full text-muted-foreground transition-colors"
              >
                <Mic className="h-5 w-5" />
              </button>
              <button
                type="submit"
                disabled={!prompt.trim() || isProcessing}
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center transition-all duration-300",
                  prompt.trim() && !isProcessing
                    ? "bg-primary text-white shadow-[0_0_15px_var(--color-primary)] hover:scale-105"
                    : "bg-white/5 text-muted-foreground cursor-not-allowed"
                )}
              >
                {isProcessing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full"
                  />
                ) : (
                  <ArrowRight className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          
          {/* Helper text / hints */}
          <AnimatePresence>
            {focused && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-4 pt-0 overflow-hidden"
              >
                <div className="h-px w-full bg-white/5 mb-3" />
                <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                  <span className="flex items-center gap-1">
                    <kbd className="bg-white/10 px-1.5 py-0.5 rounded text-white">↵</kbd> to run
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="bg-white/10 px-1.5 py-0.5 rounded text-white">ESC</kbd> to clear
                  </span>
                  <span className="ml-auto flex items-center gap-1 text-primary">
                    <Command className="h-3 w-3" /> Agent Eko v2.1 Ready
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </form>
    </div>
  );
}
