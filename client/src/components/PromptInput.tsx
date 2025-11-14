import { useState } from "react";
import { PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface PromptInputProps {
  onExecute: (prompt: string) => void;
  disabled?: boolean;
}

export function PromptInput({ onExecute, disabled }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !disabled) {
      onExecute(prompt);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative group">
        <Input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What would you like to automate?"
          disabled={disabled}
          className="h-12 px-6 pr-14 text-base rounded-lg border shadow-sm focus:shadow-md transition-shadow duration-150"
          data-testid="input-prompt"
        />
        <Button
          type="submit"
          size="icon"
          variant="ghost"
          disabled={!prompt.trim() || disabled}
          className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8"
          data-testid="button-execute"
        >
          <PlayCircle className="w-5 h-5 text-primary" />
        </Button>
      </div>
    </form>
  );
}
