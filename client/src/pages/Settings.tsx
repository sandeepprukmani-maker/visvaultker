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
import { ArrowLeft, Settings as SettingsIcon, Key, Shield } from "lucide-react";
import { useSettings, type ScreenshotMode, type AuthMode } from "@/contexts/SettingsContext";
import { Link } from "wouter";
import { Badge } from "@/components/ui/badge";

export default function Settings() {
  const { model, setModel, screenshotMode, setScreenshotMode, authMode, setAuthMode } = useSettings();

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
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                <CardTitle>Authentication Mode</CardTitle>
              </div>
              <CardDescription>
                Choose how to authenticate with AI services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={authMode} onValueChange={(value) => setAuthMode(value as AuthMode)}>
                <div className="flex items-start space-x-3 p-3 rounded-md border">
                  <RadioGroupItem value="standard" id="standard" data-testid="radio-standard-auth" className="mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="standard" className="font-medium cursor-pointer">
                        Standard API Keys
                      </Label>
                      <Badge variant="secondary">Default</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Use direct API keys (OpenAI, Anthropic, Google). Configure via environment variables.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 rounded-md border">
                  <RadioGroupItem value="oauth" id="oauth" data-testid="radio-oauth-auth" className="mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="oauth" className="font-medium cursor-pointer">
                        OAuth + Custom Gateway
                      </Label>
                      <Badge variant="outline">Enterprise</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Use OAuth authentication with custom AI gateway. Requires OAuth credentials configured in .env file.
                    </p>
                  </div>
                </div>
              </RadioGroup>
              
              {authMode === "oauth" && (
                <div className="mt-4 p-4 bg-muted/50 rounded-md border">
                  <div className="flex items-start gap-2">
                    <Key className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="space-y-2">
                      <p className="text-sm font-medium">OAuth Configuration Required</p>
                      <p className="text-sm text-muted-foreground">
                        To use OAuth mode, configure the following environment variables in your .env file:
                      </p>
                      <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                        <li><code className="bg-background px-1 py-0.5 rounded">OAUTH_TOKEN_URL</code> - Token endpoint</li>
                        <li><code className="bg-background px-1 py-0.5 rounded">OAUTH_CLIENT_ID</code> - Client ID</li>
                        <li><code className="bg-background px-1 py-0.5 rounded">OAUTH_CLIENT_SECRET</code> - Client secret</li>
                        <li><code className="bg-background px-1 py-0.5 rounded">OAUTH_GRANT_TYPE</code> - Grant type</li>
                        <li><code className="bg-background px-1 py-0.5 rounded">OAUTH_SCOPE</code> - OAuth scope</li>
                        <li><code className="bg-background px-1 py-0.5 rounded">GW_BASE_URL</code> - Gateway base URL</li>
                      </ul>
                      <p className="text-sm text-muted-foreground mt-2">
                        See <code className="bg-background px-1 py-0.5 rounded">.env.example</code> for configuration details.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

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
