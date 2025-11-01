import { Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { StatusBadge, type Status } from "./status-badge"

interface Automation {
  id: string
  command: string
  timestamp: string
  duration: string
  status: Status
  actions: number
}

interface AutomationTableProps {
  automations: Automation[]
  onView?: (id: string) => void
  onSelectAutomation?: (id: string) => void
  testId?: string
}

export function AutomationTable({ automations, onView, onSelectAutomation, testId }: AutomationTableProps) {
  return (
    <div className="rounded-md border" data-testid={testId}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Command</TableHead>
            <TableHead>Timestamp</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Actions</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {automations.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                No automations yet
              </TableCell>
            </TableRow>
          ) : (
            automations.map((automation) => (
              <TableRow key={automation.id} className="hover-elevate" data-testid={`automation-row-${automation.id}`}>
                <TableCell className="font-medium max-w-md truncate">
                  {automation.command}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground font-mono">
                  {automation.timestamp}
                </TableCell>
                <TableCell className="text-sm font-mono">{automation.duration}</TableCell>
                <TableCell className="text-sm">{automation.actions}</TableCell>
                <TableCell>
                  <StatusBadge status={automation.status} />
                </TableCell>
                <TableCell>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8"
                    onClick={() => {
                      onView?.(automation.id)
                      onSelectAutomation?.(automation.id)
                    }}
                    data-testid={`button-view-${automation.id}`}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
