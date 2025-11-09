import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Database, Loader2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { AutomationHistory } from "@shared/schema";

export default function Cache() {
  const [selectedCache, setSelectedCache] = useState<AutomationHistory | null>(null);

  const { data, isLoading } = useQuery<{ success: boolean; cache: AutomationHistory[] }>({
    queryKey: ["/api/cache"],
  });

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(date));
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const cache = data?.cache || [];

  return (
    <div className="flex h-full gap-4 p-4">
      <div className="flex-1 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Semantic Cache</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Cached automations that can be reused for similar prompts
            </p>
          </div>
          <Badge variant="secondary" className="text-sm">
            <Database className="h-3 w-3 mr-1" />
            {cache.length} cached
          </Badge>
        </div>

        {cache.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64">
              <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-muted-foreground">No cached automations yet</p>
              <p className="text-sm text-muted-foreground">
                Run some automations to build your semantic cache
              </p>
            </CardContent>
          </Card>
        ) : (
          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {cache.map((item) => (
                <Card
                  key={item.id}
                  className={`cursor-pointer transition-colors hover-elevate ${
                    selectedCache?.id === item.id ? "ring-2 ring-primary" : ""
                  }`}
                  onClick={() => setSelectedCache(item)}
                  data-testid={`cache-item-${item.id}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base truncate">{item.prompt}</CardTitle>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <Badge variant="secondary" className="text-xs">
                            <Sparkles className="h-3 w-3 mr-1" />
                            Cached
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {item.mode}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {item.model}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(item.createdAt)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  {item.detectedUrl && (
                    <CardContent className="pt-0">
                      <p className="text-sm text-muted-foreground truncate">{item.detectedUrl}</p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>

      <div className="w-96">
        {selectedCache ? (
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-base">Cache Details</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden">
              <div>
                <p className="text-sm font-medium mb-2">Prompt</p>
                <p className="text-sm text-muted-foreground border rounded-md p-3">
                  {selectedCache.prompt}
                </p>
              </div>
              
              {selectedCache.detectedUrl && (
                <div>
                  <p className="text-sm font-medium mb-2">URL</p>
                  <p className="text-sm text-muted-foreground border rounded-md p-3 truncate">
                    {selectedCache.detectedUrl}
                  </p>
                </div>
              )}

              {selectedCache.screenshot && (
                <div>
                  <p className="text-sm font-medium mb-2">Screenshot</p>
                  <img
                    src={selectedCache.screenshot}
                    alt="Cache screenshot"
                    className="w-full rounded-md border"
                    data-testid={`cache-screenshot-${selectedCache.id}`}
                  />
                </div>
              )}

              <div>
                <p className="text-sm font-medium mb-2">Generated Code</p>
                <ScrollArea className="h-48 border rounded-md p-3">
                  <pre className="text-xs">
                    <code>{selectedCache.generatedCode.typescript || "No code generated"}</code>
                  </pre>
                </ScrollArea>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                <p>
                  This automation is semantically indexed. Similar prompts will reuse this cache
                  automatically.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex items-center justify-center">
            <CardContent className="text-center">
              <p className="text-muted-foreground">Select a cache item to view details</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
