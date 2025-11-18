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
  automationMode: string;
  onAutomationModeChange: (mode: string) => void;
  screenshotMode: string;
  onScreenshotModeChange: (mode: string) => void;
}

export function SettingsPanel({ selectedModel, onModelChange, automationMode, onAutomationModeChange, screenshotMode, onScreenshotModeChange }: SettingsPanelProps) {
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
          
          <RadioGroup value={selectedModel} onValueChange={onModelChange} className="space-y-1">
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="openai" id="openai" data-testid="radio-openai" />
              <Label htmlFor="openai" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">GPT-4o Mini</div>
                <div className="text-xs text-muted-foreground">Fast and cost-effective</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="anthropic" id="anthropic" data-testid="radio-anthropic" />
              <Label htmlFor="anthropic" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Claude 3.5 Sonnet</div>
                <div className="text-xs text-muted-foreground">Advanced reasoning</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="gemini" id="gemini" data-testid="radio-gemini" />
              <Label htmlFor="gemini" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Gemini 2.0 Flash</div>
                <div className="text-xs text-muted-foreground">Multimodal capabilities</div>
              </Label>
            </div>
          </RadioGroup>

          <div className="space-y-2 pt-4 border-t">
            <h4 className="font-semibold text-base">Automation Mode</h4>
            <p className="text-sm text-muted-foreground">
              Choose how multi-step instructions are executed
            </p>
          </div>

          <RadioGroup value={automationMode} onValueChange={onAutomationModeChange} className="space-y-1">
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="act" id="act" data-testid="radio-mode-act" />
              <Label htmlFor="act" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Act Mode (Sequential)</div>
                <div className="text-xs text-muted-foreground">Fast, splits steps automatically</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="agent" id="agent" data-testid="radio-mode-agent" />
              <Label htmlFor="agent" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Agent Mode (Autonomous)</div>
                <div className="text-xs text-muted-foreground">AI-driven, handles complex workflows</div>
              </Label>
            </div>
          </RadioGroup>

          <div className="space-y-2 pt-4 border-t">
            <h4 className="font-semibold text-base">Screenshot Configuration</h4>
            <p className="text-sm text-muted-foreground">
              Choose when to capture screenshots during automation
            </p>
          </div>

          <RadioGroup value={screenshotMode} onValueChange={onScreenshotModeChange} className="space-y-1">
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="every_step" id="every_step" data-testid="radio-screenshot-every-step" />
              <Label htmlFor="every_step" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Screenshot on every step</div>
                <div className="text-xs text-muted-foreground">Capture each action</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="last_step" id="last_step" data-testid="radio-screenshot-last-step" />
              <Label htmlFor="last_step" className="flex-1 cursor-pointer font-normal">
                <div className="font-medium">Screenshot on last step</div>
                <div className="text-xs text-muted-foreground">Only final result</div>
              </Label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 rounded-lg hover-elevate">
              <RadioGroupItem value="none" id="none" data-testid="radio-screenshot-none" />
              <Label htmlFor="none" className="flex-1 cursor-pointer font-normal">
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
