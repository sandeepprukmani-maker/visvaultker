import { CrawlConfig } from "../crawl-config"

export default function CrawlConfigExample() {
  return (
    <div className="p-6 max-w-2xl">
      <CrawlConfig onStartCrawl={(url, depth) => console.log({ url, depth })} />
    </div>
  )
}
