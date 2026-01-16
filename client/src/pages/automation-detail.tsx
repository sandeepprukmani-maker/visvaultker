import { useAutomation } from "@/hooks/use-automations";
import { LogsViewer } from "@/components/logs-viewer";
import { StatusBadge } from "@/components/status-badge";
import { Layout } from "@/components/layout";
import { useRoute, Link } from "wouter";
import { ArrowLeft, ExternalLink, Image as ImageIcon, Code2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { motion } from "framer-motion";

export default function AutomationDetail() {
  const [, params] = useRoute("/automations/:id");
  const id = parseInt(params?.id || "0");
  const { data: automation, isLoading, error } = useAutomation(id);

  if (isLoading) {
    return (
      <Layout>
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-muted rounded-xl" />
            <div className="h-96 bg-muted rounded-xl" />
          </div>
        </div>
      </Layout>
    );
  }

  if (error || !automation) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <h2 className="text-2xl font-bold mb-4">Automation Not Found</h2>
          <p className="text-muted-foreground mb-8">The automation you requested doesn't exist or failed to load.</p>
          <Link href="/" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90">
            Back to Dashboard
          </Link>
        </div>
      </Layout>
    );
  }

  const logs = automation.logs || [];
  const resultJson = automation.result ? JSON.stringify(automation.result, null, 2) : null;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <Link href="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors mb-2">
              <ArrowLeft className="w-4 h-4 mr-1" /> Back to Dashboard
            </Link>
            <h1 className="text-3xl font-bold tracking-tight max-w-2xl break-words">
              {automation.prompt}
            </h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <StatusBadge status={automation.status} />
              <span>Created {formatDistanceToNow(new Date(automation.createdAt || new Date()), { addSuffix: true })}</span>
              <span className="text-xs px-2 py-0.5 bg-secondary rounded text-secondary-foreground font-mono">ID: {automation.id}</span>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          
          {/* Left Column: Logs & Result */}
          <div className="space-y-8">
            <section>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Code2 className="w-5 h-5 text-blue-400" />
                Live Execution Logs
              </h3>
              <LogsViewer logs={logs} className="h-[500px]" />
            </section>

            {resultJson && (
              <motion.section 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <ExternalLink className="w-5 h-5 text-emerald-400" />
                  Extracted Data
                </h3>
                <div className="bg-secondary/50 rounded-lg p-4 border border-border overflow-x-auto">
                  <pre className="text-sm font-mono text-emerald-300/90 whitespace-pre-wrap">{resultJson}</pre>
                </div>
              </motion.section>
            )}
          </div>

          {/* Right Column: Screenshot */}
          <div className="space-y-8">
            <section>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-purple-400" />
                Browser View
              </h3>
              
              <div className="aspect-video bg-black/40 rounded-xl border border-border/50 overflow-hidden flex items-center justify-center relative group">
                {automation.screenshot ? (
                  <motion.img 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    src={automation.screenshot} 
                    alt="Automation screenshot" 
                    className="w-full h-full object-cover object-top transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="text-center p-8">
                    <div className="w-16 h-16 rounded-full bg-white/5 mx-auto mb-4 flex items-center justify-center">
                      <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                    </div>
                    <p className="text-muted-foreground text-sm">
                      {automation.status === 'running' ? 'Waiting for screenshot...' : 'No screenshot captured'}
                    </p>
                  </div>
                )}
                
                {/* Overlay badge if running */}
                {automation.status === 'running' && (
                  <div className="absolute inset-0 bg-black/20 backdrop-blur-[1px] flex items-center justify-center">
                    <div className="bg-background/80 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 flex items-center gap-2 text-sm shadow-xl">
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                      Browser Active
                    </div>
                  </div>
                )}
              </div>
            </section>
            
            {/* Error Display */}
            {automation.error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="bg-red-500/10 border border-red-500/20 rounded-xl p-6"
              >
                <h4 className="text-red-400 font-semibold mb-2">Execution Failed</h4>
                <p className="text-red-300/80 text-sm font-mono break-all">{automation.error}</p>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
