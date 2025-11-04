import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Brain, CheckCircle, Settings } from "lucide-react";
import { useState } from "react";

export default function SettingsLLM() {
  const [defaultModel, setDefaultModel] = useState("gpt-4");

  // todo: remove mock data
  const models = [
    { id: "gpt-4", name: "GPT-4", provider: "OpenAI", capabilities: ["Text", "Vision"], enabled: true, cost: "High" },
    { id: "gpt-4-vision", name: "GPT-4 Vision", provider: "OpenAI", capabilities: ["Text", "Vision"], enabled: true, cost: "High" },
    { id: "claude-3.5", name: "Claude 3.5 Sonnet", provider: "Anthropic", capabilities: ["Text", "Vision"], enabled: true, cost: "Medium" },
    { id: "gemini-pro", name: "Gemini Pro", provider: "Google", capabilities: ["Text", "Vision"], enabled: false, cost: "Low" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">LLM Configuration</h1>
        <p className="text-muted-foreground mt-1">
          Manage AI models and their settings
        </p>
      </div>

      {/* Default Model Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            Default Model
          </CardTitle>
          <CardDescription>
            Choose the primary AI model for task interpretation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="default-model">Default Model</Label>
            <Select value={defaultModel} onValueChange={setDefaultModel}>
              <SelectTrigger id="default-model" data-testid="select-default-model">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4">GPT-4 (OpenAI)</SelectItem>
                <SelectItem value="claude-3.5">Claude 3.5 Sonnet (Anthropic)</SelectItem>
                <SelectItem value="gemini-pro">Gemini Pro (Google)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              The system will automatically select the best model based on task requirements
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Model List */}
      <Card>
        <CardHeader>
          <CardTitle>Available Models</CardTitle>
          <CardDescription>
            Configure individual AI model settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {models.map((model) => (
              <div
                key={model.id}
                className="flex items-center justify-between p-4 border rounded-lg hover-elevate"
                data-testid={`model-${model.id}`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold">{model.name}</h3>
                    <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono">
                      {model.provider}
                    </code>
                    {model.id === defaultModel && (
                      <Badge variant="default" className="text-xs">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Default
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span>Capabilities: {model.capabilities.join(", ")}</span>
                    <span>•</span>
                    <span>Cost: {model.cost}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={model.enabled}
                      onCheckedChange={(checked) => console.log(`Toggle ${model.id}:`, checked)}
                      data-testid={`switch-${model.id}`}
                    />
                    <Label className="text-sm">{model.enabled ? "Enabled" : "Disabled"}</Label>
                  </div>
                  <Button variant="ghost" size="sm" data-testid={`button-config-${model.id}`}>
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Model Selection Strategy */}
      <Card>
        <CardHeader>
          <CardTitle>Automatic Model Selection</CardTitle>
          <CardDescription>
            Configure how the system chooses models for different tasks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <p className="font-medium">Vision Tasks</p>
                <p className="text-sm text-muted-foreground">Page analysis, element detection</p>
              </div>
              <code className="text-sm">GPT-4 Vision, Claude Vision</code>
            </div>
            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <p className="font-medium">Complex Reasoning</p>
                <p className="text-sm text-muted-foreground">Workflow planning, error recovery</p>
              </div>
              <code className="text-sm">Claude 3.5 Sonnet</code>
            </div>
            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <p className="font-medium">Fast Tasks</p>
                <p className="text-sm text-muted-foreground">Simple commands, quick responses</p>
              </div>
              <code className="text-sm">GPT-4</code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
