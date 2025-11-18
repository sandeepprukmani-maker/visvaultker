import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface SettingsPanelProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
  screenshotMode: string;
  onScreenshotModeChange: (mode: string) => void;
}

export function SettingsPanel({ selectedModel, onModelChange, screenshotMode, onScreenshotModeChange }: SettingsPanelProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-10 w-10 rounded-full"
          data-testid="button-settings"
          aria-label="Settings"
        >
          <Settings className="h-5 w-5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end" data-testid="panel-settings">
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-semibold text-base">AI Model</h4>
            <p className="text-sm text-muted-foreground">
              Select which AI model to use for automation
            </p>
          </div>
          
          <RadioGroup value={selectedModel} onValueChange={onModelChange}>
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="openai" id="openai" data-testid="radio-openai" />
              <Label htmlFor="openai" className="flex-1 cursor-pointer">
                <div className="font-medium">OpenAI GPT-5</div>
                <div className="text-xs text-muted-foreground">Fast and reliable</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="anthropic" id="anthropic" data-testid="radio-anthropic" />
              <Label htmlFor="anthropic" className="flex-1 cursor-pointer">
                <div className="font-medium">Anthropic Claude</div>
                <div className="text-xs text-muted-foreground">Advanced reasoning</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="gemini" id="gemini" data-testid="radio-gemini" />
              <Label htmlFor="gemini" className="flex-1 cursor-pointer">
                <div className="font-medium">Google Gemini</div>
                <div className="text-xs text-muted-foreground">Multimodal capabilities</div>
              </Label>
            </div>
          </RadioGroup>

          <div className="space-y-2 pt-4 border-t">
            <h4 className="font-semibold text-base">Screenshot Configuration</h4>
            <p className="text-sm text-muted-foreground">
              Choose when to capture screenshots during automation
            </p>
          </div>

          <RadioGroup value={screenshotMode} onValueChange={onScreenshotModeChange}>
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="every_step" id="every_step" data-testid="radio-screenshot-every-step" />
              <Label htmlFor="every_step" className="flex-1 cursor-pointer">
                <div className="font-medium">Screenshot on every step</div>
                <div className="text-xs text-muted-foreground">Capture each action</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="last_step" id="last_step" data-testid="radio-screenshot-last-step" />
              <Label htmlFor="last_step" className="flex-1 cursor-pointer">
                <div className="font-medium">Screenshot on last step</div>
                <div className="text-xs text-muted-foreground">Only final result</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 rounded-lg p-3">
              <RadioGroupItem value="none" id="none" data-testid="radio-screenshot-none" />
              <Label htmlFor="none" className="flex-1 cursor-pointer">
                <div className="font-medium">No screenshot</div>
                <div className="text-xs text-muted-foreground">Disable screenshots</div>
              </Label>
            </div>
          </RadioGroup>
        </div>
      </PopoverContent>
    </Popover>
  );
}
