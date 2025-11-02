import { ExecutionLog } from "../execution-log"

const mockLogs = [
  {
    id: "1",
    timestamp: "14:32:20",
    action: "Navigated to /login",
    status: "success" as const,
  },
  {
    id: "2",
    timestamp: "14:32:21",
    action: 'Filled input[name="username"]',
    status: "success" as const,
  },
  {
    id: "3",
    timestamp: "14:32:22",
    action: 'Clicked button "Login"',
    status: "error" as const,
    details: "Element not found",
  },
]

export default function ExecutionLogExample() {
  return (
    <div className="p-6 h-[500px] max-w-2xl">
      <ExecutionLog logs={mockLogs} />
    </div>
  )
}
