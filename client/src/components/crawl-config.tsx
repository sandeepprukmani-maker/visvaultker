import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Play, Settings2 } from "lucide-react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

interface CrawlConfigProps {
  onStartCrawl?: (url: string, depth: number) => void
  isRunning?: boolean
  testId?: string
}

export function CrawlConfig({ onStartCrawl, isRunning = false, testId }: CrawlConfigProps) {
  const [url, setUrl] = useState("")
  const [depth, setDepth] = useState([3])
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)

  const handleStart = () => {
    if (url.trim()) {
      console.log("Starting crawl:", { url, depth: depth[0] })
      onStartCrawl?.(url, depth[0])
    }
  }

  return (
    <Card className="p-6 space-y-6" data-testid={testId}>
      <div>
        <h3 className="text-lg font-medium mb-4">Start New Crawl</h3>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url">Target URL</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              data-testid="input-url"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Crawl Depth</Label>
              <span className="text-sm text-muted-foreground">{depth[0]} levels</span>
            </div>
            <Slider
              value={depth}
              onValueChange={setDepth}
              max={10}
              min={1}
              step={1}
              data-testid="slider-depth"
            />
          </div>

          <Collapsible open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2" data-testid="button-advanced">
                <Settings2 className="h-4 w-4" />
                Advanced Options
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="waitTime">Wait Time (ms)</Label>
                <Input
                  id="waitTime"
                  type="number"
                  placeholder="1000"
                  defaultValue="1000"
                  data-testid="input-waittime"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="screenshot">Screenshot Quality</Label>
                <Input
                  id="screenshot"
                  type="number"
                  placeholder="80"
                  defaultValue="80"
                  min="1"
                  max="100"
                  data-testid="input-quality"
                />
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>

      <Button
        className="w-full gap-2"
        size="lg"
        onClick={handleStart}
        disabled={!url.trim() || isRunning}
        data-testid="button-start-crawl"
      >
        <Play className="h-4 w-4" />
        {isRunning ? "Crawling..." : "Start Crawl"}
      </Button>
    </Card>
  )
}
