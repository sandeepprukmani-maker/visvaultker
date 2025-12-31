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
        <h3 className="text-xl font-semibold mb-2">No Posters Yet</h3>
        <p className="text-muted-foreground max-w-md mx-auto">
          Generate your first social media poster from the latest news above to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
      {posters.map((item, index) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <Card className="group overflow-hidden h-full flex flex-col bg-card hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-border/50">
            <div className="relative aspect-[4/5] overflow-hidden bg-muted">
              <img
                src={item.imageUrl}
                alt={item.caption}
                className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-6">
                <Button 
                  variant="secondary" 
                  className="w-full font-semibold"
                  onClick={() => window.open(item.imageUrl, '_blank')}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download High Res
                </Button>
              </div>
            </div>
            
            <div className="p-5 flex flex-col flex-grow space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  <Calendar className="w-3 h-3" />
                  {format(new Date(item.createdAt || new Date()), "MMM d, yyyy")}
                </div>
                <h3 className="font-display font-bold text-lg leading-tight line-clamp-2 group-hover:text-primary transition-colors">
                  {item.caption}
                </h3>
              </div>
              
              <div className="mt-auto pt-4 border-t border-border/50">
                <p className="text-sm text-muted-foreground line-clamp-1">
                  Source: <span className="text-foreground font-medium">{item.post.title}</span>
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
