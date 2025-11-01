import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Search, Copy, Check } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface Element {
  id: string
  tag: string
  selector: string
  text: string
  page: string
  confidence: number
}

const mockElements: Element[] = [
  {
    id: "1",
    tag: "button",
    selector: "#login-button",
    text: "Login",
    page: "/login",
    confidence: 98,
  },
  {
    id: "2",
    tag: "input",
    selector: 'input[name="username"]',
    text: "",
    page: "/login",
    confidence: 95,
  },
  {
    id: "3",
    tag: "input",
    selector: 'input[name="password"]',
    text: "",
    page: "/login",
    confidence: 95,
  },
  {
    id: "4",
    tag: "a",
    selector: ".nav-link-profile",
    text: "My Profile",
    page: "/dashboard",
    confidence: 92,
  },
  {
    id: "5",
    tag: "button",
    selector: 'button[data-action="save"]',
    text: "Save Changes",
    page: "/settings",
    confidence: 96,
  },
]

export default function Elements() {
  const [search, setSearch] = useState("")
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const filteredElements = mockElements.filter(
    (el) =>
      el.tag.toLowerCase().includes(search.toLowerCase()) ||
      el.selector.toLowerCase().includes(search.toLowerCase()) ||
      el.text.toLowerCase().includes(search.toLowerCase()) ||
      el.page.toLowerCase().includes(search.toLowerCase())
  )

  const handleCopy = (selector: string, id: string) => {
    navigator.clipboard.writeText(selector)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Indexed Elements</h1>
        <p className="text-sm text-muted-foreground">
          All discovered interactive elements with selectors
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search elements by tag, selector, text, or page..."
          className="pl-10"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-testid="input-search-elements"
        />
      </div>

      <div className="space-y-3">
        {filteredElements.map((element) => (
          <Card key={element.id} className="p-4" data-testid={`element-${element.id}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono">
                    {element.tag}
                  </Badge>
                  {element.text && (
                    <span className="text-sm">{element.text}</span>
                  )}
                  <Badge
                    variant="secondary"
                    className={
                      element.confidence >= 95
                        ? "bg-green-500/10 text-green-700 dark:text-green-400"
                        : "bg-amber-500/10 text-amber-700 dark:text-amber-400"
                    }
                  >
                    {element.confidence}% confidence
                  </Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-muted px-2 py-1 rounded font-mono">
                    {element.selector}
                  </code>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-6 w-6"
                    onClick={() => handleCopy(element.selector, element.id)}
                    data-testid={`button-copy-${element.id}`}
                  >
                    {copiedId === element.id ? (
                      <Check className="h-3 w-3 text-green-600" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>

                <p className="text-xs text-muted-foreground">
                  Found on: <span className="font-mono">{element.page}</span>
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredElements.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No elements found matching "{search}"</p>
        </div>
      )}
    </div>
  )
}
