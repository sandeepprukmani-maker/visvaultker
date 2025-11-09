import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Sparkles } from "lucide-react";

interface UnifiedAutomationInputProps {
  onExecute: (data: { prompt: string; model: string }) => void;
  isExecuting: boolean;
}

export default function UnifiedAutomationInput({
  onExecute,
  isExecuting,
}: UnifiedAutomationInputProps) {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("google/gemini-2.5-flash");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onExecute({ prompt, model });
    }
  };

  const examples = [
    "Go to https://github.com/browserbase/stagehand and extract the star count",
    "Visit https://news.ycombinator.com and get the top 5 story titles",
    "Navigate to https://example.com and click the 'More information' link",
    "Open https://wikipedia.org, search for 'artificial intelligence', and extract the first paragraph",
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <h2 className="text-lg font-semibold">Natural Language Automation</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Describe what you want to automate in plain English. Include the website URL and your task.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="prompt" data-testid="label-prompt">
          What do you want to automate?
        </Label>
        <Textarea
          id="prompt"
          data-testid="textarea-prompt"
          placeholder="Example: Go to https://github.com and extract the trending repositories"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="min-h-32 resize-none"
          disabled={isExecuting}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="model" data-testid="label-model">
          AI Model
        </Label>
        <Select value={model} onValueChange={setModel} disabled={isExecuting}>
          <SelectTrigger id="model" data-testid="select-model">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="google/gemini-2.5-flash" data-testid="select-model-gemini">
              Google Gemini 2.5 Flash (Fast)
            </SelectItem>
            <SelectItem value="openai/gpt-4o" data-testid="select-model-gpt4o">
              OpenAI GPT-4o
            </SelectItem>
            <SelectItem value="openai/gpt-4o-mini" data-testid="select-model-gpt4o-mini">
              OpenAI GPT-4o Mini
            </SelectItem>
            <SelectItem value="anthropic/claude-sonnet-4-20250514" data-testid="select-model-claude">
              Anthropic Claude Sonnet 4
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button
        type="submit"
        data-testid="button-execute"
        className="w-full"
        disabled={isExecuting || !prompt.trim()}
      >
        {isExecuting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Automating...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            Execute Automation
          </>
        )}
      </Button>

      <div className="space-y-2">
        <Label className="text-sm text-muted-foreground">Example Prompts</Label>
        <div className="space-y-2">
          {examples.map((example, index) => (
            <button
              key={index}
              type="button"
              data-testid={`button-example-${index}`}
              onClick={() => setPrompt(example)}
              disabled={isExecuting}
              className="w-full text-left p-3 text-sm rounded-md border bg-card hover-elevate active-elevate-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
