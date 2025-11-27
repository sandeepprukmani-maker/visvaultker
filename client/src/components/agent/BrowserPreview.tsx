import { motion } from "framer-motion";
import { Globe, Lock, RotateCw, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";

interface BrowserPreviewProps {
  url: string;
  isLoading: boolean;
  content?: React.ReactNode;
}

export function BrowserPreview({ url, isLoading, content }: BrowserPreviewProps) {
  return (
    <div className="h-full flex flex-col bg-card border border-white/10 rounded-xl overflow-hidden shadow-2xl">
      {/* Browser Bar */}
      <div className="h-10 bg-[#1a1a1a] border-b border-white/5 flex items-center px-3 gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[#ff5f56]" />
          <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
          <div className="w-3 h-3 rounded-full bg-[#27c93f]" />
        </div>
        
        <div className="flex gap-2 text-muted-foreground">
          <ChevronLeft className="h-4 w-4 opacity-50" />
          <ChevronRight className="h-4 w-4 opacity-50" />
          <RotateCw className={`h-4 w-4 ${isLoading ? "animate-spin text-primary" : "opacity-50"}`} />
        </div>

        <div className="flex-1 h-7 bg-black/50 rounded flex items-center px-3 text-xs font-mono text-muted-foreground gap-2 border border-white/5">
          <Lock className="h-3 w-3 text-green-500" />
          <span className="truncate">{url || "about:blank"}</span>
        </div>
        
        <ExternalLink className="h-4 w-4 text-muted-foreground opacity-50" />
      </div>

      {/* Viewport */}
      <div className="flex-1 relative bg-white overflow-hidden">
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 z-20 bg-black/5 backdrop-blur-[1px] flex items-center justify-center"
          >
            <div className="flex flex-col items-center gap-3">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-bold text-black/70 bg-white/80 px-2 py-1 rounded shadow-sm">Loading...</span>
            </div>
          </motion.div>
        )}
        
        {/* Content Mockup */}
        <div className="w-full h-full overflow-y-auto bg-slate-50">
          {content || (
            <div className="p-8 space-y-6 opacity-30">
              {/* Skeleton UI for generic page */}
              <div className="h-8 w-1/3 bg-slate-300 rounded animate-pulse" />
              <div className="space-y-3">
                <div className="h-4 w-full bg-slate-200 rounded animate-pulse" />
                <div className="h-4 w-5/6 bg-slate-200 rounded animate-pulse" />
                <div className="h-4 w-4/6 bg-slate-200 rounded animate-pulse" />
              </div>
              <div className="h-64 w-full bg-slate-200 rounded animate-pulse mt-8" />
            </div>
          )}
        </div>

        {/* Eko Overlay */}
        <div className="absolute bottom-4 right-4 z-30 flex items-center gap-2 bg-black/80 text-white px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10 text-xs font-mono shadow-lg">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          Eko Agent Active
        </div>
      </div>
    </div>
  );
}
