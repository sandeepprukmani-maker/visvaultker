import { useQuery } from "@tanstack/react-query"
import { AutomationTable } from "@/components/automation-table"
import { CommandInput } from "@/components/command-input"
import type { Status } from "@/components/status-badge"
import type { Automation } from "@shared/schema"
import { format } from "date-fns"

export default function Automations() {
  const { data: automations = [] } = useQuery<Automation[]>({
    queryKey: ["/api/automations"],
    refetchInterval: 2000,
  })

  const automationRows = automations.map((automation) => ({
    id: automation.id,
    command: automation.command,
    timestamp: format(new Date(automation.createdAt), "yyyy-MM-dd HH:mm:ss"),
    duration: automation.duration ? `${(automation.duration / 1000).toFixed(1)}s` : "-",
    status: automation.status as Status,
    actions: automation.actionCount,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Automations</h1>
        <p className="text-sm text-muted-foreground">
          Execute and monitor all automation tasks
        </p>
      </div>

      <CommandInput />

      <div>
        <h2 className="text-lg font-medium mb-4">Automation History</h2>
        <AutomationTable automations={automationRows} testId="automation-history" />
      </div>
    </div>
  )
}
