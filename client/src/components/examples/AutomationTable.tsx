import { AutomationTable } from "../automation-table"

const mockAutomations = [
  {
    id: "1",
    command: "Login as admin",
    timestamp: "2024-11-01 14:32:18",
    duration: "2.3s",
    status: "success" as const,
    actions: 4,
  },
  {
    id: "2",
    command: "Add new user",
    timestamp: "2024-11-01 14:28:05",
    duration: "3.1s",
    status: "running" as const,
    actions: 7,
  },
]

export default function AutomationTableExample() {
  return (
    <div className="p-6 max-w-4xl">
      <AutomationTable automations={mockAutomations} />
    </div>
  )
}
