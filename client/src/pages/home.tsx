import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Video, Download, RefreshCw, Sparkles, TrendingUp, Upload, Image as ImageIcon, Trash2 } from "lucide-react";
import type { RSSItem, VideoResponse } from "@shared/routes";
import { KeyManagement } from "@/components/key-management";

export default function Home() {
  const { toast } = useToast();
  const [marketingScript, setMarketingScript] = useState<string>("");
  const [isRephrasing, setIsRephrasing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [bannerUrl, setBannerUrl] = useState<string>("/banners/current_banner.png");

  // Fetch latest RSS item
  const { data: rssItem, isLoading: rssLoading, refetch: refetchRss } = useQuery<RSSItem>({
    queryKey: ["/api/rss/latest"],
  });

  // Fetch videos list
  const { data: videos, isLoading: videosLoading } = useQuery<VideoResponse[]>({
    queryKey: ["/api/videos"],
  });

  const handleUploadBanner = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("banner", file);

    setIsUploading(true);
    try {
      const response = await fetch("/api/banners/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      const data = await response.json();
      setBannerUrl(`${data.url}?t=${Date.now()}`); // Cache bust
      toast({
        title: "Banner updated",
        description: "Your new banner will be used for all future videos.",
      });
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "There was an error uploading your banner.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Rephrase mutation
  const rephraseMutation = useMutation({
    mutationFn: async (data: { title: string; description: string }) => {
      const response = await apiRequest("POST", "/api/rss/rephrase", data);
      return response.json();
    },
    onSuccess: (data) => {
      setMarketingScript(data.marketingScript);
      toast({
        title: "Content rephrased",
        description: "Your marketing script is ready for video generation.",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to rephrase content. Please try again.",
        variant: "destructive",
      });
    },
  });

  // Create video mutation
  const createVideoMutation = useMutation({
    mutationFn: async (data: { originalTitle: string; originalDescription: string; marketingScript: string }) => {
      const response = await apiRequest("POST", "/api/videos", data);
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Video generation started",
        description: "Your video is being generated. This may take a few minutes.",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/videos"] });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to start video generation. Please try again.",
        variant: "destructive",
      });
    },
  });

  // Auto-rephrase when RSS loads
  useEffect(() => {
    if (rssItem && !marketingScript && !isRephrasing) {
      setIsRephrasing(true);
      rephraseMutation.mutate({
        title: rssItem.title,
        description: rssItem.description,
      });
    }
  }, [rssItem]);

  useEffect(() => {
    if (!rephraseMutation.isPending) {
      setIsRephrasing(false);
    }
  }, [rephraseMutation.isPending]);

  const handleGenerateVideo = () => {
    if (!rssItem || !marketingScript) return;
    
    createVideoMutation.mutate({
      originalTitle: rssItem.title,
      originalDescription: rssItem.description,
      marketingScript,
    });
  };

  const handleRefresh = () => {
    setMarketingScript("");
    refetchRss();
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl md:text-4xl font-bold flex items-center justify-center gap-3">
            <TrendingUp className="h-8 w-8 text-primary" />
            Mortgage Rate Video Generator
          </h1>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Automatically fetch the latest mortgage rate news, transform it into compelling marketing content, 
            and generate professional AI videos targeting first-time home buyers and refinancers.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-8">
            <KeyManagement />
            
            {/* Banner Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5 text-primary" />
                  Promotional Banner
                </CardTitle>
                <CardDescription>
                  This image will be overlayed at the bottom of your generated videos
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col md:flex-row items-center gap-6">
                  <div className="w-full md:w-1/2 aspect-[4/1] bg-muted rounded-md overflow-hidden border relative flex items-center justify-center">
                    <img 
                      src={bannerUrl} 
                      alt="Current Banner" 
                      className="max-w-full max-h-full object-contain"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = "https://placehold.co/720x180?text=Upload+Your+Banner";
                      }}
                    />
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm text-muted-foreground">
                      Recommended size: 720x180px (PNG with transparency supported).
                    </p>
                    <input 
                      type="file" 
                      className="hidden" 
                      ref={fileInputRef} 
                      accept="image/*"
                      onChange={handleUploadBanner}
                    />
                    <Button 
                      onClick={() => fileInputRef.current?.click()} 
                      disabled={isUploading}
                      className="w-full md:w-auto"
                      data-testid="button-upload-banner"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Upload New Banner
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Latest News Section */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    Latest Mortgage Rate News
                  </CardTitle>
                  <CardDescription>
                    Fetched from mortgagenewsdaily.com/rss/rates
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="icon" 
                  onClick={handleRefresh}
                  disabled={rssLoading}
                  data-testid="button-refresh"
                >
                  <RefreshCw className={`h-4 w-4 ${rssLoading ? "animate-spin" : ""}`} />
                </Button>
              </CardHeader>
              <CardContent>
                {rssLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : rssItem ? (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-lg" data-testid="text-rss-title">{rssItem.title}</h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        Published: {new Date(rssItem.pubDate).toLocaleDateString()}
                      </p>
                    </div>
                    <p className="text-muted-foreground" data-testid="text-rss-description">
                      {rssItem.description}
                    </p>
                    {rssItem.link && (
                      <a 
                        href={rssItem.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-primary hover:underline text-sm"
                        data-testid="link-rss-source"
                      >
                        Read full article
                      </a>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No news available</p>
                )}
              </CardContent>
            </Card>

            {/* Marketing Script Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  AI Marketing Script
                </CardTitle>
                <CardDescription>
                  Strategically rephrased for first-time home buyers and refinancers
                </CardDescription>
              </CardHeader>
              <CardContent>
                {rephraseMutation.isPending || isRephrasing ? (
                  <div className="flex items-center gap-3 py-8 justify-center">
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    <span className="text-muted-foreground">Generating marketing script with AI...</span>
                  </div>
                ) : marketingScript ? (
                  <div className="space-y-4">
                    <div className="bg-muted/50 p-4 rounded-md">
                      <p className="whitespace-pre-wrap" data-testid="text-marketing-script">{marketingScript}</p>
                    </div>
                    <div className="flex gap-3">
                      <Button
                        onClick={handleGenerateVideo}
                        disabled={createVideoMutation.isPending}
                        data-testid="button-generate-video"
                      >
                        {createVideoMutation.isPending ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Starting...
                          </>
                        ) : (
                          <>
                            <Video className="h-4 w-4 mr-2" />
                            Generate Video
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          if (rssItem) {
                            rephraseMutation.mutate({
                              title: rssItem.title,
                              description: rssItem.description,
                            });
                          }
                        }}
                        disabled={rephraseMutation.isPending}
                        data-testid="button-regenerate-script"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Regenerate Script
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground py-4">Loading marketing script...</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-8">
            {/* Generated Videos Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="h-5 w-5 text-primary" />
                  Generated Videos
                </CardTitle>
                <CardDescription>
                  Your AI-powered marketing videos
                </CardDescription>
              </CardHeader>
              <CardContent>
                {videosLoading ? (
                  <div className="grid gap-4">
                    {[1, 2].map((i) => (
                      <Skeleton key={i} className="h-48 w-full" />
                    ))}
                  </div>
                ) : videos && videos.length > 0 ? (
                  <div className="grid gap-4">
                    {videos.map((video) => (
                      <VideoCard key={video.id} video={video} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Video className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No videos generated yet.</p>
                    <p className="text-sm">Generate your first video using the button above.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function VideoCard({ video }: { video: VideoResponse }) {
  const [status, setStatus] = useState(video.status);
  const [videoUrl, setVideoUrl] = useState(video.videoUrl);
  const [thumbnailUrl, setThumbnailUrl] = useState(video.thumbnailUrl);
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { toast } = useToast();

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this video? This will also remove it from HeyGen.")) {
      return;
    }
    setIsDeleting(true);
    try {
      await apiRequest("DELETE", `/api/videos/${video.id}`);
      toast({
        title: "Video deleted",
        description: "The video has been removed.",
      });
      queryClient.invalidateQueries({ queryKey: ["/api/videos"] });
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Could not delete the video. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleReprocess = async () => {
    setIsReprocessing(true);
    try {
      const response = await apiRequest("POST", `/api/videos/${video.id}/reprocess`);
      const data = await response.json();
      if (data.videoUrl) {
        setVideoUrl(data.videoUrl + "?t=" + Date.now()); // Cache bust
        toast({
          title: "Video reprocessed",
          description: "The video has been updated with the latest banner.",
        });
      }
    } catch (error) {
      toast({
        title: "Reprocess failed",
        description: "Could not reprocess the video. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsReprocessing(false);
    }
  };

  // Poll for status if pending or processing
  useEffect(() => {
    if (status === "pending" || status === "processing") {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`/api/videos/${video.id}/status`);
          const data = await response.json();
          
          setStatus(data.status);
          if (data.videoUrl) setVideoUrl(data.videoUrl);
          if (data.thumbnailUrl) setThumbnailUrl(data.thumbnailUrl);
          
          if (data.status === "completed") {
            toast({
              title: "Video ready",
              description: "Your video has finished generating.",
            });
            queryClient.invalidateQueries({ queryKey: ["/api/videos"] });
            clearInterval(interval);
          } else if (data.status === "failed") {
            toast({
              title: "Video failed",
              description: "Video generation failed. Please try again.",
              variant: "destructive",
            });
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Error polling status:", error);
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [status, video.id, toast]);

  const getStatusBadge = () => {
    switch (status) {
      case "completed":
        return <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded-full">Completed</span>;
      case "processing":
        return <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> Processing</span>;
      case "pending":
        return <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 px-2 py-1 rounded-full">Pending</span>;
      case "failed":
        return <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-1 rounded-full">Failed</span>;
      default:
        return <span className="text-xs bg-muted px-2 py-1 rounded-full">{status}</span>;
    }
  };

  return (
    <div className="border rounded-md overflow-hidden" data-testid={`card-video-${video.id}`}>
      {/* Video Preview */}
      <div className="aspect-video bg-muted relative">
        {status === "completed" && videoUrl ? (
          <video
            src={videoUrl}
            controls
            className="w-full h-full object-cover"
            poster={thumbnailUrl || undefined}
            data-testid={`video-player-${video.id}`}
          />
        ) : thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="Video thumbnail"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            {status === "pending" || status === "processing" ? (
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Generating video...</p>
              </div>
            ) : (
              <Video className="h-12 w-12 text-muted-foreground opacity-50" />
            )}
          </div>
        )}
      </div>
      
      {/* Video Info */}
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <h4 className="font-medium text-sm truncate" data-testid={`text-video-title-${video.id}`}>
            {video.originalTitle}
          </h4>
          {getStatusBadge()}
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(video.createdAt).toLocaleString()}
        </p>
        
        <div className="flex items-center gap-3 flex-wrap">
          {status === "completed" && videoUrl && (
            <>
              <a
                href={videoUrl}
                download
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                data-testid={`link-download-${video.id}`}
              >
                <Download className="h-4 w-4" />
                Download Video
              </a>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReprocess}
                disabled={isReprocessing}
                className="text-sm"
                data-testid={`button-reprocess-${video.id}`}
              >
                {isReprocessing ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-1" />
                )}
                {isReprocessing ? "Reprocessing..." : "Reprocess"}
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-sm text-destructive hover:text-destructive"
            data-testid={`button-delete-${video.id}`}
          >
            {isDeleting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-1" />
            ) : (
              <Trash2 className="h-4 w-4 mr-1" />
            )}
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </div>
    </div>
  );
}
