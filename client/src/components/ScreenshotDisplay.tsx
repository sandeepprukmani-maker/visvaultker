import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Image as ImageIcon } from "lucide-react";

interface ScreenshotDisplayProps {
  screenshots: string[];
}

export default function ScreenshotDisplay({ screenshots }: ScreenshotDisplayProps) {
  return (
    <Card className="flex h-full flex-col border">
      <div className="flex h-10 items-center justify-between border-b px-4">
        <h3 className="text-sm font-medium">Screenshot</h3>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4">
          {screenshots.length === 0 ? (
            <div className="flex h-64 items-center justify-center border-2 border-dashed rounded-md">
              <div className="flex flex-col items-center gap-2">
                <ImageIcon className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No screenshots yet</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {screenshots.map((screenshot, index) => (
                <img
                  key={index}
                  src={screenshot}
                  alt={`Screenshot ${index + 1}`}
                  className="w-full rounded-md border"
                  data-testid={`screenshot-${index}`}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
