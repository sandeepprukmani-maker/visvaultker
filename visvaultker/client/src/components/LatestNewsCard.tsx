import { format } from "date-fns";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Clock, ExternalLink, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useGeneratePoster } from "@/hooks/use-posts";
import type { Post } from "@shared/schema";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

interface LatestNewsCardProps {
  post: Post;
}

export function LatestNewsCard({ post }: LatestNewsCardProps) {
  const generatePoster = useGeneratePoster();
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const { toast } = useToast();

  const handleGenerateVideo = async () => {
    setIsGeneratingVideo(true);
    try {
      const response = await fetch("/api/generate-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ postId: post.id })
      });
      
      if (!response.ok) throw new Error("Failed to start video generation");
      
      const data = await response.json();
      toast({
        title: "Video Generation Started",
        description: "HeyGen is processing your video. ID: " + data.video_id,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="overflow-hidden border-2 border-primary/10 bg-gradient-to-br from-white to-blue-50/50 dark:from-slate-900 dark:to-slate-800/50 shadow-xl shadow-primary/5">
        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
          <Sparkles className="w-48 h-48" />
        </div>

        <CardHeader className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-primary font-medium bg-primary/10 w-fit px-3 py-1 rounded-full">
            <Sparkles className="w-4 h-4" />
            <span>Latest Market Update</span>
          </div>
          
          <div className="space-y-2 relative z-10">
            <CardTitle className="text-3xl md:text-4xl font-display leading-tight text-foreground">
              {post.title}
            </CardTitle>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="w-4 h-4" />
              <time>{post.pubDate ? format(new Date(post.pubDate), "MMM d, yyyy • h:mm a") : "Just now"}</time>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 relative z-10">
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <p className="text-lg leading-relaxed text-muted-foreground">
              {post.content}
            </p>
          </div>

          <div className="flex flex-wrap gap-4 pt-4 border-t border-border/50">
            <Button
              size="lg"
              className="font-semibold text-base px-8 shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all"
              onClick={() => generatePoster.mutate({ postId: post.id })}
              disabled={generatePoster.isPending}
            >
              {generatePoster.isPending ? (
                <>
                  <span className="animate-spin mr-2">✨</span>
                  Generating Magic...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate Social Caption
                </>
              )}
            </Button>

            <Button
              size="lg"
              variant="secondary"
              className="font-semibold text-base px-8 shadow-lg transition-all"
              onClick={handleGenerateVideo}
              disabled={isGeneratingVideo}
            >
              {isGeneratingVideo ? (
                <>
                  <span className="animate-spin mr-2">🎬</span>
                  Processing Video...
                </>
              ) : (
                <>
                  <Video className="w-5 h-5 mr-2" />
                  Generate Social Caption Video
                </>
              )}
            </Button>
            
            <Button variant="outline" size="lg" asChild>
              <a href={post.link} target="_blank" rel="noopener noreferrer">
                Read Full Article <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
