import { History, Sparkles, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";

interface HistoryItem {
  id: string;
  prompt: string;
  status: string;
  createdAt: string;
}

interface CacheItem {
  id: string;
  prompt: string;
  useCount: string;
  lastUsed: string;
}

interface HistorySidebarProps {
  history: HistoryItem[];
  cache: CacheItem[];
  onRerun: (id: string) => void;
  onDelete: (id: string) => void;
}

export function HistorySidebar({ history, cache, onRerun, onDelete }: HistorySidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (isCollapsed) {
    return (
      <div className="h-full w-12 bg-sidebar border-r border-sidebar-border relative flex items-center justify-center group">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setIsCollapsed(false)}
          data-testid="button-expand-sidebar"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div
      className="h-full w-80 bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-250 ease-in-out"
      data-testid="sidebar-history"
    >
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-sidebar-border flex-shrink-0">
        <h2 className="font-semibold text-base">History & Cache</h2>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setIsCollapsed(true)}
          data-testid="button-collapse-sidebar"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Cache Section */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold">Cached Patterns</h3>
            <Badge variant="secondary" className="ml-auto text-xs">
              {cache.length}
            </Badge>
          </div>
        </div>
        
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-2 mb-4">
            {cache.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-8">
                No cached patterns yet
              </div>
            ) : (
              cache.map((item) => (
                <Card
                  key={item.id}
                  className="p-3 hover-elevate cursor-pointer transition-all"
                  onClick={() => onRerun(item.id)}
                  data-testid={`cache-item-${item.id}`}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.prompt}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Used {item.useCount}x • {new Date(item.lastUsed).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>

          <Separator className="my-4" />

          {/* History Section */}
          <div className="flex items-center gap-2 mb-3">
            <History className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Recent Executions</h3>
            <Badge variant="secondary" className="ml-auto text-xs">
              {history.length}
            </Badge>
          </div>

          <div className="space-y-2 pb-4">
            {history.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-8">
                No executions yet
              </div>
            ) : (
              history.map((item) => (
                <Card
                  key={item.id}
                  className="p-3 hover-elevate transition-all"
                  data-testid={`history-item-${item.id}`}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.prompt}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant={item.status === "success" ? "default" : "destructive"}
                          className="text-xs"
                        >
                          {item.status}
                        </Badge>
                        <p className="text-xs text-muted-foreground">
                          {new Date(item.createdAt).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRerun(item.id);
                        }}
                        data-testid={`button-rerun-${item.id}`}
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(item.id);
                        }}
                        data-testid={`button-delete-${item.id}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
