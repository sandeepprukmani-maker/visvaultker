import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Globe, PlayCircle, Layout, TrendingUp } from "lucide-react"
import { CommandInput } from "@/components/command-input"
import { MetricCard } from "@/components/metric-card"
import { AutomationTable } from "@/components/automation-table"
import { ExecutionLog } from "@/components/execution-log"
import type { Status } from "@/components/status-badge"
import type { Automation, AutomationLog } from "@shared/schema"
import { format } from "date-fns"

export default function Dashboard() {
  const [selectedAutomationId, setSelectedAutomationId] = useState<string | null>(null)

  const { data: stats } = useQuery({
    queryKey: ["/api/stats"],
    refetchInterval: 5000,
  })

  const { data: automations = [] } = useQuery<Automation[]>({
    queryKey: ["/api/automations"],
    refetchInterval: 2000,
  })

  const { data: logs = [] } = useQuery<AutomationLog[]>({
    queryKey: ["/api/automations", selectedAutomationId, "logs"],
    enabled: !!selectedAutomationId,
    refetchInterval: 1000,
  })

  useEffect(() => {
    if (automations.length > 0 && !selectedAutomationId) {
      setSelectedAutomationId(automations[0].id)
    }
  }, [automations, selectedAutomationId])

  const metrics = [
    {
      title: "Pages Crawled",
      value: stats?.pagesCrawled?.toString() || "0",
      icon: Layout,
      description: "Discovered pages",
    },
    {
      title: "Elements Indexed",
      value: stats?.elementsIndexed?.toString() || "0",
      icon: Globe,
      description: "Ready for automation",
    },
    {
      title: "Automations Run",
      value: automations.length.toString(),
      icon: PlayCircle,
      description: "Total executions",
    },
    {
      title: "Success Rate",
      value: stats?.successRate || "0%",
      icon: TrendingUp,
      description: "Overall performance",
    },
  ]

  const automationRows = automations.map((automation) => ({
    id: automation.id,
    command: automation.command,
    timestamp: format(new Date(automation.createdAt), "yyyy-MM-dd HH:mm:ss"),
    duration: automation.duration ? `${(automation.duration / 1000).toFixed(1)}s` : "-",
    status: automation.status as Status,
    actions: automation.actionCount,
  }))

  const logRows = logs.map((log) => ({
    id: log.id,
    timestamp: format(new Date(log.timestamp), "HH:mm:ss"),
    action: log.action,
    status: log.status as Status,
    details: log.details || undefined,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Command your automation with natural language
        </p>
      </div>

      <CommandInput />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, i) => (
          <MetricCard
            key={i}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            description={metric.description}
            testId={`metric-${i}`}
          />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 space-y-4">
          <h2 className="text-lg font-medium">Recent Automations</h2>
          <AutomationTable 
            automations={automationRows} 
            testId="automation-table"
            onSelectAutomation={setSelectedAutomationId}
          />
        </div>

        <div className="lg:col-span-2 h-[500px]">
          <ExecutionLog logs={logRows} testId="execution-log" />
        </div>
      </div>
    </div>
  )
}
