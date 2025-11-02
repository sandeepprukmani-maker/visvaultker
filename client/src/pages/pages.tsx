import { useState } from "react"
import { PageCard } from "@/components/page-card"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

const mockPages = [
  {
    id: "1",
    title: "Login Page",
    url: "/login",
    elementCount: 12,
    templateGroup: 0,
  },
  {
    id: "2",
    title: "User Dashboard",
    url: "/dashboard",
    elementCount: 48,
    templateGroup: 0,
  },
  {
    id: "3",
    title: "User Profile",
    url: "/profile/john-doe",
    elementCount: 32,
    templateGroup: 5,
  },
  {
    id: "4",
    title: "Settings - General",
    url: "/settings",
    elementCount: 28,
    templateGroup: 3,
  },
  {
    id: "5",
    title: "Product List",
    url: "/products",
    elementCount: 64,
    templateGroup: 8,
  },
  {
    id: "6",
    title: "Product Details",
    url: "/products/item-123",
    elementCount: 42,
    templateGroup: 8,
  },
]

export default function Pages() {
  const [search, setSearch] = useState("")

  const filteredPages = mockPages.filter(
    (page) =>
      page.title.toLowerCase().includes(search.toLowerCase()) ||
      page.url.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Crawled Pages</h1>
        <p className="text-sm text-muted-foreground">
          Browse and analyze all discovered pages
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search pages..."
          className="pl-10"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-testid="input-search-pages"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredPages.map((page) => (
          <PageCard
            key={page.id}
            title={page.title}
            url={page.url}
            elementCount={page.elementCount}
            templateGroup={page.templateGroup || undefined}
            testId={`page-card-${page.id}`}
          />
        ))}
      </div>

      {filteredPages.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No pages found matching "{search}"</p>
        </div>
      )}
    </div>
  )
}
