import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Play, Settings } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type AutomationMode = "act" | "observe" | "extract" | "agent";

interface AutomationInputProps {
  onExecute: (data: {
    url: string;
    prompt: string;
    mode: AutomationMode;
    model?: string;
  }) => void;
  isExecuting?: boolean;
}

export default function AutomationInput({ onExecute, isExecuting = false }: AutomationInputProps) {
  const [url, setUrl] = useState("https://");
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<AutomationMode>("act");
  const [model, setModel] = useState("google/gemini-2.5-flash");
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const handleExecute = () => {
    if (url && prompt) {
      onExecute({ url, prompt, mode, model });
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-2">
        <Label htmlFor="url" className="text-sm font-medium">
          Target URL
        </Label>
        <Input
          id="url"
          data-testid="input-url"
          type="url"
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="h-12 font-mono text-sm"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="prompt" className="text-sm font-medium">
          Natural Language Prompt
        </Label>
        <Textarea
          id="prompt"
          data-testid="input-prompt"
          placeholder="Describe what you want to automate... (e.g., 'Click the login button and fill the form')"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="min-h-24 resize-none font-sans"
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-medium">Automation Mode</Label>
        <RadioGroup
          value={mode}
          onValueChange={(value) => setMode(value as AutomationMode)}
          className="grid grid-cols-4 gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="act" id="mode-act" data-testid="radio-act" />
            <Label htmlFor="mode-act" className="cursor-pointer font-normal">
              Act
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="observe" id="mode-observe" data-testid="radio-observe" />
            <Label htmlFor="mode-observe" className="cursor-pointer font-normal">
              Observe
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="extract" id="mode-extract" data-testid="radio-extract" />
            <Label htmlFor="mode-extract" className="cursor-pointer font-normal">
              Extract
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="agent" id="mode-agent" data-testid="radio-agent" />
            <Label htmlFor="mode-agent" className="cursor-pointer font-normal">
              Agent
            </Label>
          </div>
        </RadioGroup>
      </div>

      <Collapsible open={isConfigOpen} onOpenChange={setIsConfigOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2"
            data-testid="button-config-toggle"
          >
            <Settings className="h-4 w-4" />
            Advanced Configuration
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="model" className="text-sm font-medium">
              Model
            </Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger id="model" data-testid="select-model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google/gemini-2.5-flash">Google Gemini 2.5 Flash</SelectItem>
                <SelectItem value="google/gemini-2.5-pro">Google Gemini 2.5 Pro</SelectItem>
                <SelectItem value="anthropic/claude-sonnet-4-20250514">Anthropic Claude Sonnet 4</SelectItem>
                <SelectItem value="openai/gpt-4o">OpenAI GPT-4o</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Button
        onClick={handleExecute}
        disabled={!url || !prompt || isExecuting}
        className="h-10 w-full gap-2"
        data-testid="button-execute"
      >
        <Play className="h-4 w-4" />
        {isExecuting ? "Executing..." : "Execute Automation"}
      </Button>
    </div>
  );
}
