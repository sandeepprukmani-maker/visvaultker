import { Card } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface BrowserPreviewProps {
  isLoading?: boolean;
  currentUrl?: string;
}

export default function BrowserPreview({ isLoading = false, currentUrl }: BrowserPreviewProps) {
  return (
    <Card className="flex h-full flex-col overflow-hidden border">
      <div className="flex h-10 items-center gap-2 border-b bg-muted/30 px-4">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-destructive/60" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
          <div className="h-3 w-3 rounded-full bg-green-500/60" />
        </div>
        {currentUrl && (
          <div className="ml-4 flex-1 truncate font-mono text-xs text-muted-foreground">
            {currentUrl}
          </div>
        )}
      </div>
      <div className="relative flex flex-1 items-center justify-center bg-background">
        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading browser session...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="text-6xl text-muted-foreground/20">🌐</div>
            <p className="text-sm text-muted-foreground">
              Browser preview will appear here
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
