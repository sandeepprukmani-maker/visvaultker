import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Globe, Play, CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp, Lock } from "lucide-react"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Textarea } from "@/components/ui/textarea"

export default function Crawl() {
  const [url, setUrl] = useState("")
  const [depth, setDepth] = useState(3)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [authType, setAuthType] = useState<"none" | "basic" | "cookie" | "form">("none")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [cookieData, setCookieData] = useState("")
  const { toast } = useToast()

  const { data: sessions = [] } = useQuery<CrawlSession[]>({
    queryKey: ["/api/crawl"],
    refetchInterval: 3000,
  })

  const startCrawlMutation = useMutation({
    mutationFn: async (data: { url: string; depth: number; options?: any }) => {
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
      setUsername("")
      setPassword("")
      setCookieData("")
      setAuthType("none")
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

    const options: any = {}

    if (authType === "basic" && username && password) {
      const urlObj = new URL(crawlUrl)
      options.proxy = {
        server: `${urlObj.protocol}//${urlObj.host}`,
        username,
        password,
      }
    } else if (authType === "cookie" && cookieData) {
      try {
        const cookies = JSON.parse(cookieData)
        options.cookies = Array.isArray(cookies) ? cookies : [cookies]
      } catch (error) {
        toast({
          title: "Invalid Cookie Format",
          description: "Please provide valid JSON format for cookies",
          variant: "destructive",
        })
        return
      }
    }

    startCrawlMutation.mutate({ 
      url: crawlUrl, 
      depth,
      ...(Object.keys(options).length > 0 && { options })
    })
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
                  if (e.key === "Enter" && !showAdvanced) {
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

          <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                className="w-full justify-between"
                data-testid="button-toggle-advanced"
              >
                <span className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Advanced Options (Authentication)
                </span>
                {showAdvanced ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="auth-type">Authentication Type</Label>
                <Select value={authType} onValueChange={(value: any) => setAuthType(value)}>
                  <SelectTrigger id="auth-type" data-testid="select-auth-type">
                    <SelectValue placeholder="Select authentication method" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None (Public Website)</SelectItem>
                    <SelectItem value="basic">HTTP Basic Auth</SelectItem>
                    <SelectItem value="cookie">Cookie-Based Auth</SelectItem>
                    <SelectItem value="form">Form Login (Use Automation)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {authType === "basic" && (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      placeholder="Enter username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      data-testid="input-username"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      data-testid="input-password"
                    />
                  </div>
                </div>
              )}

              {authType === "cookie" && (
                <div className="space-y-2">
                  <Label htmlFor="cookie-data">Cookie JSON</Label>
                  <Textarea
                    id="cookie-data"
                    placeholder='{"name": "session_id", "value": "abc123", "domain": ".example.com"}'
                    value={cookieData}
                    onChange={(e) => setCookieData(e.target.value)}
                    className="font-mono text-sm"
                    rows={4}
                    data-testid="input-cookie-data"
                  />
                  <p className="text-xs text-muted-foreground">
                    Provide cookie(s) as JSON object or array of objects
                  </p>
                </div>
              )}

              {authType === "form" && (
                <div className="rounded-lg border bg-muted/50 p-4 space-y-2">
                  <p className="text-sm font-medium">How to use Form Login:</p>
                  <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                    <li>First, crawl the login page (without authentication)</li>
                    <li>Go to the Automations tab</li>
                    <li>Create an automation like: "Login as admin with password mypassword"</li>
                    <li>After successful login, crawl protected pages</li>
                  </ol>
                </div>
              )}
            </CollapsibleContent>
          </Collapsible>
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
