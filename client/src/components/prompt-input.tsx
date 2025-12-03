import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sparkles, Send, Loader2 } from "lucide-react";
import { SiAnthropic, SiOpenai } from "react-icons/si";
import type { ModelOption } from "@shared/schema";

interface PromptInputProps {
  onSubmit: (prompt: string, model: ModelOption) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const EXAMPLE_PROMPTS = [
  "Scrape product prices from Amazon",
  "Fill out a contact form automatically",
  "Extract all email addresses from a webpage",
  "Research competitors and create a report",
];

const QUICK_ACTIONS = [
  { label: "Web Scraping", prompt: "Scrape data from " },
  { label: "Form Filling", prompt: "Fill out the form at " },
  { label: "Data Extraction", prompt: "Extract all " },
  { label: "Research", prompt: "Research about " },
];

export function PromptInput({ onSubmit, isLoading = false, disabled = false }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState<ModelOption>("anthropic");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [prompt]);

  const handleSubmit = () => {
    if (prompt.trim() && !isLoading && !disabled) {
      onSubmit(prompt.trim(), model);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickAction = (actionPrompt: string) => {
    setPrompt(actionPrompt);
    textareaRef.current?.focus();
  };

  return (
    <div className="mx-auto w-full max-w-3xl space-y-4">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          What would you like to automate?
        </h1>
        <p className="text-muted-foreground">
          Describe your task in natural language and Eko will create a workflow for you
        </p>
      </div>

      <div
        className={`relative rounded-xl border-2 bg-card p-1 transition-all duration-200 ${
          isFocused
            ? "border-transparent ring-2 ring-purple-500/50 shadow-lg shadow-purple-500/10"
            : "border-border"
        }`}
      >
        <div className="flex items-start gap-3 p-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/10 to-blue-500/10">
            <Sparkles className="h-5 w-5 text-purple-500" />
          </div>
          <div className="flex-1">
            <Textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your automation task..."
              className="min-h-[80px] resize-none border-0 bg-transparent text-base focus-visible:ring-0 focus-visible:ring-offset-0"
              disabled={isLoading || disabled}
              data-testid="input-prompt"
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 border-t px-3 py-2">
          <div className="flex flex-wrap items-center gap-2">
            {QUICK_ACTIONS.map((action) => (
              <Badge
                key={action.label}
                variant="secondary"
                className="cursor-pointer text-xs"
                onClick={() => handleQuickAction(action.prompt)}
                data-testid={`badge-quick-action-${action.label.toLowerCase().replace(" ", "-")}`}
              >
                {action.label}
              </Badge>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={model}
              onValueChange={(value) => setModel(value as ModelOption)}
              disabled={isLoading || disabled}
            >
              <SelectTrigger 
                className="w-[160px]" 
                data-testid="select-model"
              >
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="anthropic" data-testid="select-item-anthropic">
                  <div className="flex items-center gap-2">
                    <SiAnthropic className="h-4 w-4" />
                    <span>Claude</span>
                  </div>
                </SelectItem>
                <SelectItem value="openai" data-testid="select-item-openai">
                  <div className="flex items-center gap-2">
                    <SiOpenai className="h-4 w-4" />
                    <span>GPT-4o-mini</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleSubmit}
              disabled={!prompt.trim() || isLoading || disabled}
              size="sm"
              className="bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600"
              data-testid="button-submit-prompt"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Planning...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Generate
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-center text-sm text-muted-foreground">Try these examples:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {EXAMPLE_PROMPTS.map((example) => (
            <button
              key={example}
              onClick={() => setPrompt(example)}
              className="rounded-full border bg-background px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              data-testid={`button-example-${example.slice(0, 20).replace(/\s/g, "-").toLowerCase()}`}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
