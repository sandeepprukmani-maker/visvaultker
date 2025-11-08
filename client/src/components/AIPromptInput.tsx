import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface AIPromptInputProps {
  onGenerate?: (prompt: string) => void;
  isGenerating?: boolean;
}

export function AIPromptInput({ onGenerate, isGenerating }: AIPromptInputProps) {
  const [prompt, setPrompt] = useState("");

  const handleGenerate = () => {
    if (prompt.trim() && onGenerate) {
      onGenerate(prompt);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary" />
        <h3 className="text-sm font-medium">AI-Powered Automation Generator</h3>
      </div>
      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe what you want to automate in plain English...&#10;&#10;Example: Go to Amazon, search for 'wireless headphones', filter by 4+ stars, and screenshot the first 3 results"
        className="min-h-32 resize-none text-sm"
        disabled={isGenerating}
        data-testid="textarea-ai-prompt"
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Press <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">⌘</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> to generate
        </p>
        <Button 
          onClick={handleGenerate}
          disabled={!prompt.trim() || isGenerating}
          data-testid="button-generate-automation"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Automation
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
