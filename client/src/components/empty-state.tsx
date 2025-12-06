import { Bot, Sparkles, MousePointer2, Type, Navigation } from "lucide-react";
import { Card } from "@/components/ui/card";

interface EmptyStateProps {
  onExampleClick: (prompt: string) => void;
}

const examples = [
  {
    icon: Navigation,
    prompt: "Go to google.com and search for 'weather today'",
    label: "Navigate & Search",
  },
  {
    icon: MousePointer2,
    prompt: "Navigate to github.com and click on the Sign in button",
    label: "Navigate & Click",
  },
  {
    icon: Type,
    prompt: "Go to example.com and take a screenshot of the page",
    label: "Screenshot",
  },
];

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6">
        <Bot className="h-8 w-8 text-primary" />
      </div>
      
      <h2 className="text-2xl font-semibold mb-2 text-center">
        Browser Automation Assistant
      </h2>
      
      <p className="text-muted-foreground text-center max-w-md mb-8">
        Describe what you want to automate in plain language. I'll handle the 
        browser interactions for you using Playwright.
      </p>

      <div className="w-full max-w-lg">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">
            Try an example
          </span>
        </div>
        
        <div className="flex flex-col gap-3">
          {examples.map((example) => (
            <Card
              key={example.prompt}
              className="p-4 cursor-pointer hover-elevate active-elevate-2"
              onClick={() => onExampleClick(example.prompt)}
              data-testid={`example-${example.label.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-9 h-9 rounded-md bg-muted">
                  <example.icon className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium mb-0.5">{example.label}</p>
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {example.prompt}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
