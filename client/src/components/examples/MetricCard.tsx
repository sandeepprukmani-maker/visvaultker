import { MetricCard } from "../metric-card"
import { Globe } from "lucide-react"

export default function MetricCardExample() {
  return (
    <div className="p-6 grid gap-4 md:grid-cols-2 max-w-4xl">
      <MetricCard
        title="Pages Crawled"
        value="247"
        icon={Globe}
        description="Across 3 sites"
        trend={{ value: 12, isPositive: true }}
      />
      <MetricCard
        title="Success Rate"
        value="94.2%"
        icon={Globe}
        trend={{ value: 2, isPositive: false }}
      />
    </div>
  )
}
