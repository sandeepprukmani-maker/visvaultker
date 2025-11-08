import { useState } from "react";
import { RefreshCw, ArrowLeft, ArrowRight, Monitor, Smartphone, Tablet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface BrowserPreviewProps {
  url?: string;
  screenshot?: string;
  isLoading?: boolean;
}

export function BrowserPreview({ url = "https://example.com", screenshot, isLoading }: BrowserPreviewProps) {
  const [currentUrl, setCurrentUrl] = useState(url);
  const [viewport, setViewport] = useState("desktop");

  const handleRefresh = () => {
    console.log("Refresh clicked");
  };

  const handleBack = () => {
    console.log("Back clicked");
  };

  const handleForward = () => {
    console.log("Forward clicked");
  };

  return (
    <div className="flex flex-col h-full bg-card border border-card-border rounded-md">
      <div className="flex items-center gap-2 p-3 border-b border-card-border">
        <Button size="icon" variant="ghost" onClick={handleBack} data-testid="button-back">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <Button size="icon" variant="ghost" onClick={handleForward} data-testid="button-forward">
          <ArrowRight className="w-4 h-4" />
        </Button>
        <Button size="icon" variant="ghost" onClick={handleRefresh} data-testid="button-refresh">
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
        <Input
          value={currentUrl}
          onChange={(e) => setCurrentUrl(e.target.value)}
          className="flex-1 h-9 text-sm font-mono"
          placeholder="Enter URL"
          data-testid="input-url"
        />
        <Select value={viewport} onValueChange={setViewport}>
          <SelectTrigger className="w-32 h-9" data-testid="select-viewport">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desktop">
              <div className="flex items-center gap-2">
                <Monitor className="w-4 h-4" />
                <span>Desktop</span>
              </div>
            </SelectItem>
            <SelectItem value="tablet">
              <div className="flex items-center gap-2">
                <Tablet className="w-4 h-4" />
                <span>Tablet</span>
              </div>
            </SelectItem>
            <SelectItem value="mobile">
              <div className="flex items-center gap-2">
                <Smartphone className="w-4 h-4" />
                <span>Mobile</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="flex-1 overflow-auto bg-muted/20 p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="space-y-4 w-full max-w-md">
              <div className="h-4 bg-muted rounded animate-pulse" />
              <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
              <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
            </div>
          </div>
        ) : screenshot ? (
          <img src={screenshot} alt="Browser preview" className="w-full rounded border border-border" data-testid="img-screenshot" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2">
              <Monitor className="w-12 h-12 text-muted-foreground mx-auto" />
              <p className="text-sm text-muted-foreground">No preview available</p>
              <p className="text-xs text-muted-foreground">Run an automation to see the browser preview</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
