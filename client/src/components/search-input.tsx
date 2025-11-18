import { Mic, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState, FormEvent } from "react";

interface SearchInputProps {
  onSubmit: (prompt: string) => void;
  isExecuting?: boolean;
  centered?: boolean;
}

export function SearchInput({ onSubmit, isExecuting = false, centered = true }: SearchInputProps) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isExecuting) {
      onSubmit(prompt.trim());
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`w-full max-w-2xl transition-all duration-300 ${
        centered ? "mx-auto" : ""
      }`}
    >
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-primary/10 to-primary/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-300" />
        
        <div className="relative flex items-center gap-2 bg-card border border-border rounded-full shadow-lg hover:shadow-xl focus-within:shadow-xl transition-shadow duration-200 px-6 py-3">
          <Mic className="h-5 w-5 text-muted-foreground flex-shrink-0" />
          
          <Input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder=""
            className="flex-1 border-0 focus-visible:ring-0 bg-transparent text-base placeholder:text-muted-foreground"
            disabled={isExecuting}
            data-testid="input-prompt"
            aria-label="Automation prompt"
          />
          
          <Button
            type="submit"
            size="sm"
            disabled={!prompt.trim() || isExecuting}
            className="rounded-full px-4 gap-1.5"
            data-testid="button-execute"
          >
            <Sparkles className="h-4 w-4" />
            <span className="font-medium">Execute</span>
          </Button>
        </div>
      </div>
    </form>
  );
}
