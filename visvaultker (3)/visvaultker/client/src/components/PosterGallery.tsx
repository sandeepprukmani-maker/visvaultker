import { motion } from "framer-motion";
import { Download, Share2, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { format } from "date-fns";
import type { Poster, Post } from "@shared/schema";

interface PosterGalleryProps {
  posters: (Poster & { post: Post })[];
}

export function PosterGallery({ posters }: PosterGalleryProps) {
  if (posters.length === 0) {
    return (
      <div className="text-center py-24 bg-muted/30 rounded-3xl border border-dashed border-muted-foreground/20">
        <div className="bg-background w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
          <Share2 className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-semibold mb-2">No Captions Yet</h3>
        <p className="text-muted-foreground max-w-md mx-auto">
          Generate your first social media caption from the latest news above to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
      {posters.map((item, index) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <Card className="group overflow-hidden h-full flex flex-col bg-card hover:shadow-xl transition-all duration-300 border-border/50">
            <div className="p-6 flex flex-col flex-grow space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Calendar className="w-3 h-3" />
                    {format(new Date(item.createdAt || new Date()), "MMM d, yyyy")}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => {
                      navigator.clipboard.writeText(item.caption);
                      alert("Caption copied to clipboard!");
                    }}
                  >
                    <Share2 className="w-4 h-4" />
                  </Button>
                </div>
                
                <div className="relative">
                  <p className="text-lg font-medium leading-relaxed italic text-foreground/90 bg-muted/30 p-4 rounded-xl border border-border/50">
                    "{item.caption}"
                  </p>
                </div>
              </div>
              
              <div className="mt-auto pt-4 border-t border-border/50">
                <p className="text-xs text-muted-foreground">
                  Inspired by: <span className="text-foreground font-medium">{item.post.title}</span>
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
