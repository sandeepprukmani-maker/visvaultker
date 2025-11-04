import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Maximize2, Minimize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface BrowserPreviewProps {
  url?: string;
  isLoading?: boolean;
}

export function BrowserPreview({ url = "about:blank", isLoading = false }: BrowserPreviewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  return (
    <Card className="flex flex-col h-full">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-red-500" />
            <div className="h-3 w-3 rounded-full bg-yellow-500" />
            <div className="h-3 w-3 rounded-full bg-green-500" />
          </div>
          <code className="text-xs text-muted-foreground truncate font-mono">{url}</code>
          {isLoading && (
            <Badge variant="outline" className="text-xs">
              Loading...
            </Badge>
          )}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setIsFullscreen(!isFullscreen)}
          data-testid="button-toggle-fullscreen"
        >
          {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </Button>
      </div>
      <div className="flex-1 bg-background relative overflow-hidden" data-testid="browser-preview">
        <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <p className="text-sm">Browser Preview</p>
            <p className="text-xs mt-1">Live automation view will appear here</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
