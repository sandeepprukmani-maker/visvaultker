import { useState, useRef } from "react";
import { useQuotes, useGenerateQuote } from "@/hooks/use-quotes";
import { PosterCard } from "@/components/PosterCard";
import { Button } from "@/components/ui/button";
import { Wand2, History, AlertCircle, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useToast } from "@/hooks/use-toast";
import html2canvas from "html2canvas";

export default function Home() {
  const { data: quotes, isLoading: isListLoading } = useQuotes();
  const generateMutation = useGenerateQuote();
  const { toast } = useToast();
  const posterRef = useRef<HTMLDivElement>(null);
  
  // Local state to show immediate feedback before refetch
  const [currentQuote, setCurrentQuote] = useState<{caption: string, author: string | null} | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (!posterRef.current) return;
    
    try {
      setIsDownloading(true);
      const canvas = await html2canvas(posterRef.current, {
        backgroundColor: "#FFC107",
        scale: 2,
      });
      
      const link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = `quote-poster-${Date.now()}.png`;
      link.click();
      
      toast({
        title: "Downloaded",
        description: "Your poster has been saved.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to download poster.",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleGenerate = () => {
    generateMutation.mutate(
      { postId: 1 },
      {
        onSuccess: (data) => {
          setCurrentQuote(data);
          toast({
            title: "Quote Generated",
            description: "Fresh inspiration served hot.",
          });
        },
        onError: (error) => {
          toast({
            variant: "destructive",
            title: "Error",
            description: error.message,
          });
        }
      }
    );
  };

  // Determine what to show in the main hero area
  const heroQuote = currentQuote || (quotes && quotes.length > 0 ? quotes[0] : null);
  const isHeroLoading = generateMutation.isPending || (!heroQuote && isListLoading);

  return (
    <div className="min-h-screen bg-[#FFC107] text-[#004D40] font-body selection:bg-[#004D40] selection:text-[#FFC107]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 p-6 flex justify-between items-center bg-[#FFC107]/90 backdrop-blur-sm border-b border-[#004D40]/10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[#004D40] flex items-center justify-center text-[#FFC107] font-display font-black text-xl">
            Q
          </div>
          <h1 className="font-display font-bold text-xl tracking-tight">QUOTE<span className="font-light opacity-70">POSTER</span></h1>
        </div>
        <a 
          href="https://github.com" 
          target="_blank" 
          rel="noreferrer"
          className="text-sm font-bold uppercase tracking-widest hover:underline opacity-60 hover:opacity-100 transition-opacity"
        >
          GitHub
        </a>
      </header>

      <main className="pt-32 pb-20 px-4 md:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-24 items-start">
          
          {/* Left Column: Hero Poster */}
          <div className="lg:col-span-7 flex flex-col gap-8 sticky top-32">
            <motion.div 
              ref={posterRef}
              layout
              className="w-full max-w-2xl mx-auto shadow-[20px_20px_0px_0px_rgba(0,77,64,0.15)] bg-white"
            >
              {isHeroLoading ? (
                <PosterCard caption="" isLoading={true} />
              ) : heroQuote ? (
                <PosterCard 
                  caption={heroQuote.caption} 
                  author={heroQuote.author} 
                  key={heroQuote.caption} // Force re-render for animation
                />
              ) : (
                <div className="aspect-[4/5] bg-[#FFC107] border-4 border-[#004D40] border-dashed flex flex-col items-center justify-center p-8 text-center opacity-50">
                  <AlertCircle size={48} className="mb-4" />
                  <p className="font-display font-bold text-xl">No quotes yet</p>
                  <p>Generate your first masterpiece.</p>
                </div>
              )}
            </motion.div>

            <div className="flex flex-col gap-4 justify-center">
              <Button 
                onClick={handleGenerate} 
                disabled={generateMutation.isPending}
                size="lg"
                className="w-full text-lg h-20"
              >
                {generateMutation.isPending ? (
                  <span className="animate-pulse">Crafting...</span>
                ) : (
                  <>
                    <Wand2 className="mr-3 h-6 w-6" />
                    Generate New Poster
                  </>
                )}
              </Button>
              <Button 
                onClick={handleDownload}
                disabled={!heroQuote || isDownloading}
                variant="outline"
                size="lg"
                className="w-full text-lg h-14"
              >
                {isDownloading ? (
                  <span className="animate-pulse">Saving...</span>
                ) : (
                  <>
                    <Download className="mr-3 h-6 w-6" />
                    Download Poster
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Right Column: History */}
          <div className="lg:col-span-5 flex flex-col gap-8 mt-12 lg:mt-0">
            <div className="flex items-center gap-3 pb-4 border-b-4 border-[#004D40]">
              <History className="h-6 w-6" />
              <h2 className="text-2xl font-black uppercase tracking-tight">Recent Archives</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6">
              {isListLoading && !quotes && (
                <div className="animate-pulse flex flex-col gap-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-32 bg-[#004D40]/5 w-full rounded-none" />
                  ))}
                </div>
              )}

              <AnimatePresence mode="popLayout">
                {quotes?.map((quote) => (
                  <motion.div
                    key={quote.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="group relative cursor-pointer"
                    onClick={() => setCurrentQuote(quote)}
                  >
                    <div className="absolute -inset-2 bg-[#004D40] opacity-0 group-hover:opacity-10 transition-opacity -z-10 transform skew-x-[-2deg]" />
                    <div className="bg-white p-6 shadow-lg border-l-8 border-[#004D40] hover:translate-x-1 transition-transform">
                      <p className="font-display font-bold text-lg leading-tight line-clamp-2 mb-2">
                        "{quote.caption}"
                      </p>
                      <p className="text-xs font-bold tracking-widest opacity-60 uppercase">
                        — {quote.author || "Unknown"}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {quotes?.length === 0 && !isListLoading && (
                <div className="text-center p-8 border-2 border-[#004D40]/10 border-dashed">
                  <p className="opacity-60 font-medium">Your archive is empty.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
