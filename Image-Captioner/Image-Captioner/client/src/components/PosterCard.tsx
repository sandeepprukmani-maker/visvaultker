import { Quote as QuoteIcon } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface PosterCardProps {
  caption: string;
  author?: string | null;
  className?: string;
  isLoading?: boolean;
}

export function PosterCard({ caption, author, className, isLoading }: PosterCardProps) {
  return (
    <div 
      className={cn(
        "relative aspect-[4/5] w-full overflow-hidden bg-[#FFC107] text-[#004D40] shadow-2xl transition-all duration-300 bg-grain",
        className
      )}
    >
      <div className="absolute inset-4 border-2 border-[#004D40]/20 pointer-events-none z-20" />
      
      <div className="flex h-full flex-col justify-between p-8 sm:p-12 relative z-30">
        {/* Top Icon */}
        <div className="mb-4">
          <QuoteIcon 
            size={64} 
            className="text-[#004D40] opacity-20 rotate-180" 
            strokeWidth={3}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex items-center justify-center">
          {isLoading ? (
            <div className="flex flex-col items-center gap-4 w-full">
              <div className="h-8 bg-[#004D40]/10 w-3/4 animate-pulse rounded" />
              <div className="h-8 bg-[#004D40]/10 w-full animate-pulse rounded" />
              <div className="h-8 bg-[#004D40]/10 w-5/6 animate-pulse rounded" />
            </div>
          ) : (
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="font-display font-black text-4xl sm:text-5xl md:text-6xl uppercase leading-[0.9] text-center tracking-tighter break-words hyphens-auto"
            >
              {caption}
            </motion.p>
          )}
        </div>

        {/* Footer/Author */}
        <div className="mt-8">
          {isLoading ? (
             <div className="h-4 bg-[#004D40]/10 w-1/3 mx-auto animate-pulse rounded mt-2" />
          ) : (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center justify-center gap-4 opacity-80"
            >
              <div className="h-[2px] w-8 sm:w-16 bg-[#004D40]" />
              <span className="font-display font-bold tracking-widest text-sm sm:text-base uppercase whitespace-nowrap">
                {author || "Unknown"}
              </span>
              <div className="h-[2px] w-8 sm:w-16 bg-[#004D40]" />
            </motion.div>
          )}
        </div>
      </div>

      {/* Decorative large faint text/shape behind */}
      <div className="absolute -bottom-20 -right-20 opacity-5 pointer-events-none">
        <QuoteIcon size={400} />
      </div>
    </div>
  );
}
