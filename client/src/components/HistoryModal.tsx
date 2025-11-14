import { X, Clock, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { AutomationHistory } from "@shared/schema";

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplay: (prompt: string) => void;
}

export function HistoryModal({ isOpen, onClose, onReplay }: HistoryModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const { data: history = [], isLoading } = useQuery<AutomationHistory[]>({
    queryKey: ["/api/history"],
    enabled: isOpen,
  });

  const filteredHistory = history.filter((item) =>
    item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimeAgo = (date: Date | string) => {
    const d = new Date(date);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    return "Just now";
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-96 p-0">
        <SheetHeader className="p-6 pb-4 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-lg font-medium">Automation History</SheetTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8"
              data-testid="button-close-history"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </SheetHeader>

        <div className="p-6 pt-4">
          <Input
            type="search"
            placeholder="Search history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10"
            data-testid="input-search-history"
          />
        </div>

        <ScrollArea className="h-[calc(100vh-180px)]">
          <div className="px-6 space-y-3 pb-6">
            {isLoading ? (
              <div className="text-center py-12">
                <p className="text-sm text-muted-foreground">Loading history...</p>
              </div>
            ) : filteredHistory.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 mx-auto text-muted-foreground mb-3 opacity-50" />
                <p className="text-sm text-muted-foreground" data-testid="text-no-history">
                  {searchQuery ? "No matching history found" : "No automation history yet"}
                </p>
              </div>
            ) : (
              filteredHistory.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-lg border hover-elevate group cursor-pointer"
                  onClick={() => onReplay(item.prompt)}
                  data-testid={`history-item-${item.id}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm line-clamp-2 mb-2" data-testid={`text-prompt-${item.id}`}>
                        {item.prompt}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span data-testid={`text-time-${item.id}`}>
                          {item.createdAt ? formatTimeAgo(item.createdAt) : "Unknown"}
                        </span>
                        {item.status === "success" && (
                          <span className="text-green-600">✓ Success</span>
                        )}
                        {item.status === "error" && (
                          <span className="text-red-600">✗ Failed</span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                      data-testid={`button-replay-${item.id}`}
                    >
                      <Play className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
