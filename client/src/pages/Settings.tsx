import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Settings as SettingsIcon } from "lucide-react";
import { useSettings, type ScreenshotMode } from "@/contexts/SettingsContext";
import { Link } from "wouter";

export default function Settings() {
  const { model, setModel, screenshotMode, setScreenshotMode } = useSettings();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background px-6">
        <div className="flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="icon" data-testid="button-back">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <SettingsIcon className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-lg font-semibold">Settings</h1>
            <p className="text-xs text-muted-foreground">Configure your preferences</p>
          </div>
        </div>
      </header>

      <main className="container max-w-4xl py-8 px-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>AI Model Configuration</CardTitle>
              <CardDescription>
                Select the AI model to use for browser automation tasks
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="model" data-testid="label-model">
                  AI Model
                </Label>
                <Select value={model} onValueChange={setModel}>
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
                <p className="text-sm text-muted-foreground">
                  Your selection will be saved automatically and used for all automation tasks
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Screenshot Configuration</CardTitle>
              <CardDescription>
                Configure when to capture screenshots during automation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={screenshotMode} onValueChange={(value) => setScreenshotMode(value as ScreenshotMode)}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="every-step" id="every-step" data-testid="radio-every-step" />
                  <Label htmlFor="every-step" className="font-normal cursor-pointer">
                    Screenshot on every step
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="last-step" id="last-step" data-testid="radio-last-step" />
                  <Label htmlFor="last-step" className="font-normal cursor-pointer">
                    Screenshot on last step
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="none" id="none" data-testid="radio-none" />
                  <Label htmlFor="none" className="font-normal cursor-pointer">
                    No screenshot
                  </Label>
                </div>
              </RadioGroup>
              <p className="text-sm text-muted-foreground mt-4">
                Your selection will be saved automatically and applied to all automation tasks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model Information</CardTitle>
              <CardDescription>
                Learn about the available AI models
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <p className="text-sm font-medium">Google Gemini 2.5 Flash</p>
                <p className="text-sm text-muted-foreground">
                  Fast and efficient model, great for most automation tasks
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">OpenAI GPT-4o</p>
                <p className="text-sm text-muted-foreground">
                  Advanced reasoning capabilities for complex automation scenarios
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">OpenAI GPT-4o Mini</p>
                <p className="text-sm text-muted-foreground">
                  Lightweight version with good balance of speed and capability
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Anthropic Claude Sonnet 4</p>
                <p className="text-sm text-muted-foreground">
                  Excellent for nuanced understanding and precise automation
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
