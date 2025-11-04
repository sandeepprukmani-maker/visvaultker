import { WebsiteProfileCard } from "@/components/website-profile-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Globe, Zap, Shield } from "lucide-react";
import { useState } from "react";

export default function Learn() {
  const [url, setUrl] = useState("");
  const [isLearning, setIsLearning] = useState(false);

  const handleLearn = () => {
    console.log("Learning website:", url);
    setIsLearning(true);
    setTimeout(() => setIsLearning(false), 3000);
  };

  // todo: remove mock data
  const learnedWebsites = [
    {
      id: "linkedin",
      url: "linkedin.com",
      elementCount: 247,
      lastLearned: "2 days ago",
      version: 3,
      status: "learned" as const,
    },
    {
      id: "twitter",
      url: "twitter.com",
      elementCount: 189,
      lastLearned: "1 week ago",
      version: 2,
      status: "outdated" as const,
    },
    {
      id: "amazon",
      url: "amazon.com",
      elementCount: 412,
      lastLearned: "3 days ago",
      version: 1,
      status: "learned" as const,
    },
    {
      id: "github",
      url: "github.com",
      elementCount: 156,
      lastLearned: "5 days ago",
      version: 4,
      status: "learned" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Learn Websites</h1>
        <p className="text-muted-foreground mt-1">
          Teach AI to understand website structures and elements
        </p>
      </div>

      {/* Learn New Website */}
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
              />
              <Button
                onClick={handleLearn}
                disabled={!url || isLearning}
                data-testid="button-start-learning"
              >
                {isLearning ? "Learning..." : "Start Learning"}
              </Button>
            </div>
          </div>

          {/* Learning Features */}
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
                <p className="text-sm font-medium">Interactive Exploration</p>
                <p className="text-xs text-muted-foreground">
                  Discovers hidden elements through hover and click
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="text-sm font-medium">Safe Mode</p>
                <p className="text-xs text-muted-foreground">
                  Read-only exploration, no destructive actions
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Learned Websites */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Learned Websites ({learnedWebsites.length})</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {learnedWebsites.map((website) => (
            <WebsiteProfileCard
              key={website.id}
              {...website}
              onView={() => console.log("View profile", website.id)}
              onRelearn={() => console.log("Relearn website", website.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
