import { ExternalLink, Eye, RotateCw } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface PageCardProps {
  title: string
  url: string
  elementCount: number
  screenshot?: string
  templateGroup?: number
  onView?: () => void
  onRecrawl?: () => void
  testId?: string
}

export function PageCard({
  title,
  url,
  elementCount,
  screenshot,
  templateGroup,
  onView,
  onRecrawl,
  testId,
}: PageCardProps) {
  return (
    <Card className="overflow-hidden hover-elevate" data-testid={testId}>
      <div className="aspect-video bg-muted relative overflow-hidden">
        {screenshot ? (
          <img src={screenshot} alt={title} className="w-full h-full object-cover" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <ExternalLink className="h-8 w-8 text-muted-foreground" />
          </div>
        )}
        {templateGroup && (
          <Badge className="absolute top-2 right-2" variant="secondary">
            {templateGroup} similar
          </Badge>
        )}
      </div>
      <div className="p-4 space-y-3">
        <div>
          <h3 className="font-medium truncate" data-testid={`${testId}-title`}>{title}</h3>
          <p className="text-xs text-muted-foreground truncate font-mono" data-testid={`${testId}-url`}>
            {url}
          </p>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground" data-testid={`${testId}-elements`}>
            {elementCount} elements
          </span>
          <div className="flex gap-1">
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8"
              onClick={() => {
                console.log("View details:", title)
                onView?.()
              }}
              data-testid={`${testId}-view`}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8"
              onClick={() => {
                console.log("Recrawl:", title)
                onRecrawl?.()
              }}
              data-testid={`${testId}-recrawl`}
            >
              <RotateCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
