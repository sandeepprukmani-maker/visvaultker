import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Globe, Play, CheckCircle, XCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { apiRequest, queryClient } from "@/lib/queryClient"
import type { CrawlSession } from "@shared/schema"
import { format } from "date-fns"

export default function Crawl() {
  const [url, setUrl] = useState("")
  const [depth, setDepth] = useState(3)
  const { toast } = useToast()

  const { data: sessions = [] } = useQuery<CrawlSession[]>({
    queryKey: ["/api/crawl"],
    refetchInterval: 3000,
  })

  const startCrawlMutation = useMutation({
    mutationFn: async (data: { url: string; depth: number }) => {
      const response = await apiRequest("POST", "/api/crawl", data)
      return await response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/crawl"] })
      queryClient.invalidateQueries({ queryKey: ["/api/stats"] })
      toast({
        title: "Crawl Started",
        description: "Website crawling has begun",
      })
      setUrl("")
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to start crawl",
        variant: "destructive",
      })
    },
  })

  const handleStartCrawl = () => {
    if (!url.trim()) return

    let crawlUrl = url.trim()
    if (!crawlUrl.startsWith("http://") && !crawlUrl.startsWith("https://")) {
      crawlUrl = `https://${crawlUrl}`
    }

    startCrawlMutation.mutate({ url: crawlUrl, depth })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <Globe className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive"> = {
      completed: "default",
      running: "secondary",
      failed: "destructive",
      pending: "secondary",
    }
    return (
      <Badge variant={variants[status] || "secondary"}>
        {status}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Web Crawler</h1>
        <p className="text-sm text-muted-foreground">
          Crawl websites to build knowledge for automation
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Start New Crawl</CardTitle>
          <CardDescription>
            Enter a website URL to discover pages and interactive elements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_auto_auto]">
            <div className="space-y-2">
              <Label htmlFor="url">Website URL</Label>
              <Input
                id="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleStartCrawl()
                  }
                }}
                data-testid="input-url"
              />
            </div>
            <div className="space-y-2 w-32">
              <Label htmlFor="depth">Depth</Label>
              <Input
                id="depth"
                type="number"
                min="1"
                max="5"
                value={depth}
                onChange={(e) => setDepth(parseInt(e.target.value) || 3)}
                data-testid="input-depth"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleStartCrawl}
                disabled={!url.trim() || startCrawlMutation.isPending}
                data-testid="button-start-crawl"
              >
                <Play className="h-4 w-4 mr-2" />
                {startCrawlMutation.isPending ? "Starting..." : "Start Crawl"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Crawl History</CardTitle>
          <CardDescription>Recent website crawls and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>URL</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Pages</TableHead>
                  <TableHead>Elements</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      No crawls yet. Start your first crawl above.
                    </TableCell>
                  </TableRow>
                ) : (
                  sessions.map((session) => (
                    <TableRow key={session.id} data-testid={`crawl-session-${session.id}`}>
                      <TableCell className="font-medium max-w-md truncate">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(session.status)}
                          <span className="truncate">{session.url}</span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(session.status)}</TableCell>
                      <TableCell className="font-mono text-sm">
                        {session.pagesFound}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {session.elementsFound}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground font-mono">
                        {format(new Date(session.startedAt), "MMM dd, HH:mm")}
                      </TableCell>
                      <TableCell className="text-sm font-mono">
                        {session.completedAt
                          ? `${Math.round((new Date(session.completedAt).getTime() - new Date(session.startedAt).getTime()) / 1000)}s`
                          : "-"}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
