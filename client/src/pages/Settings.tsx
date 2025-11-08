import { Settings as SettingsIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export default function Settings() {
  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold">Settings</h2>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-2xl space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Playwright Configuration</CardTitle>
              <CardDescription>Configure browser automation settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="browser-type">Default Browser</Label>
                <Input id="browser-type" defaultValue="chromium" data-testid="input-browser-type" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Headless Mode</Label>
                  <p className="text-xs text-muted-foreground">Run browser without UI</p>
                </div>
                <Switch data-testid="switch-headless" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Slow Motion</Label>
                  <p className="text-xs text-muted-foreground">Add delay between actions</p>
                </div>
                <Switch data-testid="switch-slow-motion" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">AI Integration</CardTitle>
              <CardDescription>Configure OpenAI API settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-key">OpenAI API Key</Label>
                <Input id="api-key" type="password" placeholder="sk-..." data-testid="input-api-key" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Input id="model" defaultValue="gpt-4" data-testid="input-model" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recording Settings</CardTitle>
              <CardDescription>Configure browser recording options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto-generate Code</Label>
                  <p className="text-xs text-muted-foreground">Automatically create Playwright code from recordings</p>
                </div>
                <Switch defaultChecked data-testid="switch-auto-generate" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Capture Screenshots</Label>
                  <p className="text-xs text-muted-foreground">Save screenshots during recording</p>
                </div>
                <Switch defaultChecked data-testid="switch-screenshots" />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button data-testid="button-save-settings">Save Settings</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
