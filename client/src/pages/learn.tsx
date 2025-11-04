import { WebsiteProfileCard } from "@/components/website-profile-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Globe, Zap, Shield } from "lucide-react";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function Learn() {
  const [url, setUrl] = useState("");
  const { toast } = useToast();

  const { data: profiles, isLoading } = useQuery({
    queryKey: ["/api/python/api/website-profiles"],
  });

  const learnMutation = useMutation({
    mutationFn: async (url: string) => {
      return await apiRequest("/api/python/api/website-profiles", {
        method: "POST",
        body: JSON.stringify({ url }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/python/api/website-profiles"] });
      queryClient.invalidateQueries({ queryKey: ["/api/python/api/analytics/overview"] });
      toast({
        title: "Learning Complete",
        description: "The website has been analyzed and profiled successfully.",
      });
      setUrl("");
    },
    onError: (error: any) => {
      toast({
        title: "Learning Failed",
        description: error.message || "Failed to learn website",
        variant: "destructive",
      });
    },
  });

  const handleLearn = () => {
    if (!url) {
      toast({
        title: "URL Required",
        description: "Please enter a valid website URL",
        variant: "destructive",
      });
      return;
    }

    let formattedUrl = url.trim();
    if (!formattedUrl.startsWith("http://") && !formattedUrl.startsWith("https://")) {
      formattedUrl = "https://" + formattedUrl;
    }

    learnMutation.mutate(formattedUrl);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Learn Websites</h1>
        <p className="text-muted-foreground mt-1">
          Teach AI to understand website structures and elements
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Learn New Website
          </CardTitle>
          <CardDescription>
            Enter a URL to start the intelligent learning process
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="website-url">Website URL</Label>
            <div className="flex gap-2">
              <Input
                id="website-url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                data-testid="input-website-url"
                disabled={learnMutation.isPending}
              />
              <Button
                onClick={handleLearn}
                disabled={!url || learnMutation.isPending}
                data-testid="button-start-learning"
              >
                {learnMutation.isPending ? "Learning..." : "Start Learning"}
              </Button>
            </div>
            {learnMutation.isPending && (
              <p className="text-sm text-muted-foreground">
                This may take 30-60 seconds as AI explores the website...
              </p>
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-3 pt-4">
            <div className="flex items-start gap-3">
              <Globe className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="text-sm font-medium">Complete DOM Mapping</p>
                <p className="text-xs text-muted-foreground">
                  Maps all elements, buttons, forms, and navigation
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Zap className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="text-sm font-medium">Visual AI Analysis</p>
                <p className="text-xs text-muted-foreground">
                  Uses vision models to understand page layouts
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="text-sm font-medium">Safe Exploration</p>
                <p className="text-xs text-muted-foreground">
                  Avoids destructive actions like logout or delete
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-2xl font-semibold mb-4">Learned Websites</h2>
        {isLoading ? (
          <Card>
            <CardContent className="p-6 text-center">
              Loading profiles...
            </CardContent>
          </Card>
        ) : (profiles || []).length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-muted-foreground">
              No websites learned yet. Learn your first website to get started!
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(profiles || []).map((profile: any) => (
              <WebsiteProfileCard
                key={profile.id}
                id={profile.id}
                url={profile.url}
                elementCount={profile.dom_structure ? 100 : 0}
                lastLearned={new Date(profile.last_explored).toLocaleDateString()}
                version={profile.version}
                status="learned"
                onRelearn={() => learnMutation.mutate(profile.url)}
                onViewProfile={() => toast({ title: "View profile feature coming soon!" })}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
