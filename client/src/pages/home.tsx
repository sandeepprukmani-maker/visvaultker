import { useState } from "react";
import { Layout } from "@/components/layout";
import { useAutomations, useCreateAutomation } from "@/hooks/use-automations";
import { StatusBadge } from "@/components/status-badge";
import { Link, useLocation } from "wouter";
import { formatDistanceToNow } from "date-fns";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Terminal, ArrowRight, Sparkles } from "lucide-react";
import { clsx } from "clsx";

export default function Home() {
  const [, setLocation] = useLocation();
  const [prompt, setPrompt] = useState("");
  const { data: automations, isLoading } = useAutomations();
  const { mutate: createAutomation, isPending } = useCreateAutomation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    createAutomation(
      { prompt },
      {
        onSuccess: (data) => {
          setLocation(`/automations/${data.id}`);
        },
      }
    );
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-16">
        
        {/* Hero / Input Section */}
        <section className="text-center space-y-8 py-10">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-br from-white via-white/90 to-white/50 bg-clip-text text-transparent pb-2">
              Automate the Web
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Describe your task in plain English. Stagehand will control a headless browser to execute it, extract data, and verify results.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="relative max-w-2xl mx-auto group">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500 opacity-50" />
            <div className="relative bg-background rounded-2xl border border-white/10 shadow-2xl overflow-hidden focus-within:border-white/20 transition-colors">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Go to GitHub trending and list the top 3 repos..."
                className="w-full bg-transparent px-6 py-5 text-lg placeholder:text-muted-foreground/50 focus:outline-none font-medium"
                autoFocus
              />
              <div className="absolute right-2 top-2 bottom-2">
                <button
                  type="submit"
                  disabled={isPending || !prompt.trim()}
                  className={clsx(
                    "h-full px-6 rounded-xl font-semibold flex items-center gap-2 transition-all duration-200",
                    isPending || !prompt.trim()
                      ? "bg-secondary text-muted-foreground cursor-not-allowed"
                      : "bg-primary text-primary-foreground hover:opacity-90 hover:scale-[1.02] shadow-lg shadow-white/5"
                  )}
                >
                  {isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Run
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </section>

        {/* Recent Automations List */}
        <section className="space-y-6">
          <div className="flex items-center justify-between border-b border-white/5 pb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Terminal className="w-5 h-5 text-muted-foreground" />
              Recent Automations
            </h2>
            <span className="text-sm text-muted-foreground">{automations?.length || 0} runs</span>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-secondary/30 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid gap-4">
              <AnimatePresence>
                {automations?.map((automation) => (
                  <motion.div
                    key={automation.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <Link href={`/automations/${automation.id}`}>
                      <div className="group bg-card hover:bg-secondary/40 border border-border/50 hover:border-border rounded-xl p-5 transition-all duration-200 flex items-center justify-between cursor-pointer">
                        <div className="flex items-center gap-4 overflow-hidden">
                          <div className={clsx(
                            "w-10 h-10 rounded-lg flex items-center justify-center shrink-0 border transition-colors",
                            automation.status === 'running' 
                              ? "bg-blue-500/10 border-blue-500/20 text-blue-500" 
                              : "bg-secondary border-white/5 text-muted-foreground group-hover:bg-background"
                          )}>
                            <Play className="w-4 h-4 fill-current" />
                          </div>
                          <div className="min-w-0">
                            <h3 className="font-medium truncate pr-4 text-base group-hover:text-primary transition-colors">
                              {automation.prompt}
                            </h3>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                              <StatusBadge status={automation.status} />
                              <span>{formatDistanceToNow(new Date(automation.createdAt || new Date()), { addSuffix: true })}</span>
                            </div>
                          </div>
                        </div>
                        
                        <ArrowRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {automations?.length === 0 && (
                <div className="text-center py-12 border border-dashed border-white/10 rounded-xl bg-white/5">
                  <p className="text-muted-foreground">No automations run yet. Try running one above!</p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}
