import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"

export default function Settings() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Configure your automation platform
        </p>
      </div>

      <Card className="p-6 space-y-6">
        <div>
          <h3 className="text-lg font-medium mb-4">API Configuration</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="openai">OpenAI API Key</Label>
              <Input
                id="openai"
                type="password"
                placeholder="sk-..."
                data-testid="input-openai-key"
              />
              <p className="text-xs text-muted-foreground">
                Used for semantic understanding and intent recognition
              </p>
            </div>
          </div>
        </div>

        <Separator />

        <div>
          <h3 className="text-lg font-medium mb-4">Crawl Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-generate screenshots</Label>
                <p className="text-xs text-muted-foreground">
                  Capture visual context during crawls
                </p>
              </div>
              <Switch defaultChecked data-testid="switch-screenshots" />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable template detection</Label>
                <p className="text-xs text-muted-foreground">
                  Group similar pages automatically
                </p>
              </div>
              <Switch defaultChecked data-testid="switch-templates" />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Parallel crawling</Label>
                <p className="text-xs text-muted-foreground">
                  Crawl multiple pages simultaneously for speed
                </p>
              </div>
              <Switch defaultChecked data-testid="switch-parallel" />
            </div>
          </div>
        </div>

        <Separator />

        <div>
          <h3 className="text-lg font-medium mb-4">Automation</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Self-healing selectors</Label>
                <p className="text-xs text-muted-foreground">
                  Automatically find alternative elements when selectors break
                </p>
              </div>
              <Switch defaultChecked data-testid="switch-self-healing" />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Learning from failures</Label>
                <p className="text-xs text-muted-foreground">
                  Store failed attempts to improve future success
                </p>
              </div>
              <Switch defaultChecked data-testid="switch-learning" />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <Button data-testid="button-save-settings">Save Changes</Button>
        </div>
      </Card>
    </div>
  )
}
