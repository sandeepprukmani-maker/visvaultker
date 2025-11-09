import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Loader2, Sparkles } from "lucide-react";
import { useSettings } from "@/contexts/SettingsContext";

interface UnifiedAutomationInputProps {
  onExecute: (data: { prompt: string; model: string }) => void;
  isExecuting: boolean;
}

export default function UnifiedAutomationInput({
  onExecute,
  isExecuting,
}: UnifiedAutomationInputProps) {
  const [prompt, setPrompt] = useState("");
  const { model } = useSettings();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onExecute({ prompt, model });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <h2 className="text-lg font-semibold">Natural Language Automation</h2>
        </div>
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
    </form>
  );
}
