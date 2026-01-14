import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Video } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Video as VideoIcon, Play, RefreshCw } from "lucide-react";
import { useEffect } from "react";

export function ContentLibrary() {
  const queryClient = useQueryClient();
  const { data: videos, isLoading } = useQuery<Video[]>({
    queryKey: ["/api/videos"],
    refetchInterval: (query) => {
      // Poll if any video is still processing
      const data = query.state.data;
      const anyProcessing = Array.isArray(data) && data.some((v: any) => v.status === "processing");
      return anyProcessing ? 5000 : false;
    }
  });

  // Effect to trigger status check for processing videos
  useEffect(() => {
    if (videos) {
      videos.forEach(video => {
        if (video.status === "processing") {
          fetch(`/api/video-status/${video.videoId}`).then(() => {
            queryClient.invalidateQueries({ queryKey: ["/api/videos"] });
          });
        }
      });
    }
  }, [videos, queryClient]);

  if (isLoading) {
    return <Loader2 className="h-8 w-8 animate-spin mx-auto" />;
  }

  if (!videos?.length) {
    return (
      <Card className="bg-muted/50 border-dashed">
        <CardContent className="py-10 text-center text-muted-foreground">
          <VideoIcon className="h-10 w-10 mx-auto mb-2 opacity-20" />
          <p>No videos generated yet. Try generating one from the news cards!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {videos.map((video) => (
        <Card key={video.id} className="overflow-hidden">
          <CardHeader className="p-4 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium truncate max-w-[150px]">
              Video #{video.videoId.slice(-6)}
            </CardTitle>
            <Badge 
              variant={video.status === "completed" ? "default" : video.status === "failed" ? "destructive" : "secondary"}
              className="capitalize"
            >
              {video.status === "processing" && <RefreshCw className="h-3 w-3 animate-spin mr-1" />}
              {video.status}
            </Badge>
          </CardHeader>
          <CardContent className="p-0">
            {video.status === "completed" && video.videoUrl ? (
              <div className="aspect-[9/16] bg-black relative group">
                <video 
                  src={video.videoUrl} 
                  poster={video.thumbnailUrl || ""}
                  className="w-full h-full object-cover"
                  controls
                />
              </div>
            ) : (
              <div className="aspect-[9/16] bg-muted flex flex-col items-center justify-center p-6 text-center">
                {video.status === "processing" ? (
                  <>
                    <RefreshCw className="h-12 w-12 text-primary animate-spin mb-4" />
                    <h3 className="font-semibold mb-1">Rendering Video...</h3>
                    <p className="text-sm text-muted-foreground">
                      HeyGen is currently generating your social media short. This usually takes 2-3 minutes.
                    </p>
                  </>
                ) : (
                  <>
                    <VideoIcon className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="font-semibold mb-1">Generation Failed</h3>
                    <p className="text-sm text-muted-foreground">
                      Something went wrong with this video generation.
                    </p>
                  </>
                )}
              </div>
            )}
            {video.script && (
              <div className="p-4 border-t">
                <p className="text-xs text-muted-foreground line-clamp-3 italic">
                  &quot;{video.script}&quot;
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
