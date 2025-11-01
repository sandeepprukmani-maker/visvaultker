import { AutomationTable } from "@/components/automation-table"
import { CommandInput } from "@/components/command-input"
import type { Status } from "@/components/status-badge"

const mockAutomations = [
  {
    id: "1",
    command: "Login as admin",
    timestamp: "2024-11-01 14:32:18",
    duration: "2.3s",
    status: "success" as Status,
    actions: 4,
  },
  {
    id: "2",
    command: "Add new user with email test@example.com",
    timestamp: "2024-11-01 14:28:05",
    duration: "3.1s",
    status: "success" as Status,
    actions: 7,
  },
  {
    id: "3",
    command: "Search for John Doe and verify profile",
    timestamp: "2024-11-01 14:15:42",
    duration: "1.8s",
    status: "running" as Status,
    actions: 3,
  },
  {
    id: "4",
    command: "Delete test product from inventory",
    timestamp: "2024-11-01 13:58:21",
    duration: "4.2s",
    status: "error" as Status,
    actions: 5,
  },
  {
    id: "5",
    command: "Update user profile settings",
    timestamp: "2024-11-01 13:45:10",
    duration: "2.8s",
    status: "success" as Status,
    actions: 6,
  },
  {
    id: "6",
    command: "Export data to CSV format",
    timestamp: "2024-11-01 13:22:33",
    duration: "5.4s",
    status: "success" as Status,
    actions: 8,
  },
  {
    id: "7",
    command: "Create 5 test products with random data",
    timestamp: "2024-11-01 12:58:47",
    duration: "12.1s",
    status: "success" as Status,
    actions: 25,
  },
  {
    id: "8",
    command: "Verify email notifications are working",
    timestamp: "2024-11-01 12:34:15",
    duration: "3.6s",
    status: "warning" as Status,
    actions: 4,
  },
]

export default function Automations() {
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
        <AutomationTable automations={mockAutomations} testId="automation-history" />
      </div>
    </div>
  )
}
