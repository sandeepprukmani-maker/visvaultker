import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"

interface AppSettings {
  apiKey?: string;
  autoScreenshots: boolean;
  templateDetection: boolean;
  parallelCrawling: boolean;
  selfHealing: boolean;
  learningFromFailures: boolean;
}

export default function Settings() {
  const { toast } = useToast()
  const [apiKey, setApiKey] = useState("")
  const [autoScreenshots, setAutoScreenshots] = useState(true)
  const [templateDetection, setTemplateDetection] = useState(true)
  const [parallelCrawling, setParallelCrawling] = useState(true)
  const [selfHealing, setSelfHealing] = useState(true)
  const [learningFromFailures, setLearningFromFailures] = useState(true)

  const { data: settings } = useQuery<AppSettings>({
    queryKey: ['/api/settings'],
  })

  useEffect(() => {
    if (settings) {
      setApiKey(settings.apiKey || "")
      setAutoScreenshots(settings.autoScreenshots)
      setTemplateDetection(settings.templateDetection)
      setParallelCrawling(settings.parallelCrawling)
      setSelfHealing(settings.selfHealing)
      setLearningFromFailures(settings.learningFromFailures)
    }
  }, [settings])

  const saveSettingsMutation = useMutation({
    mutationFn: async (newSettings: Partial<AppSettings>) => {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings),
      })
      if (!response.ok) throw new Error('Failed to save settings')
      return response.json()
    },
    onSuccess: () => {
      toast({
        title: "Settings saved",
        description: "Your settings have been updated successfully.",
      })
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to save settings. Please try again.",
        variant: "destructive",
      })
    },
  })

  const handleSave = () => {
    saveSettingsMutation.mutate({
      apiKey: apiKey || undefined,
      autoScreenshots,
      templateDetection,
      parallelCrawling,
      selfHealing,
      learningFromFailures,
    })
  }

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
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
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
              <Switch 
                checked={autoScreenshots} 
                onCheckedChange={setAutoScreenshots}
                data-testid="switch-screenshots" 
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable template detection</Label>
                <p className="text-xs text-muted-foreground">
                  Group similar pages automatically
                </p>
              </div>
              <Switch 
                checked={templateDetection} 
                onCheckedChange={setTemplateDetection}
                data-testid="switch-templates" 
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Parallel crawling</Label>
                <p className="text-xs text-muted-foreground">
                  Crawl multiple pages simultaneously for speed
                </p>
              </div>
              <Switch 
                checked={parallelCrawling} 
                onCheckedChange={setParallelCrawling}
                data-testid="switch-parallel" 
              />
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
              <Switch 
                checked={selfHealing} 
                onCheckedChange={setSelfHealing}
                data-testid="switch-self-healing" 
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Learning from failures</Label>
                <p className="text-xs text-muted-foreground">
                  Store failed attempts to improve future success
                </p>
              </div>
              <Switch 
                checked={learningFromFailures} 
                onCheckedChange={setLearningFromFailures}
                data-testid="switch-learning" 
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <Button 
            onClick={handleSave}
            disabled={saveSettingsMutation.isPending}
            data-testid="button-save-settings"
          >
            {saveSettingsMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </Card>
    </div>
  )
}
