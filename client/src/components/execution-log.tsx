import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Download, Filter } from "lucide-react"
import { StatusBadge, type Status } from "./status-badge"

interface LogEntry {
  id: string
  timestamp: string
  action: string
  status: Status
  details?: string
}

interface ExecutionLogProps {
  logs: LogEntry[]
  title?: string
  testId?: string
}

export function ExecutionLog({ logs, title = "Execution Log", testId }: ExecutionLogProps) {
  const [filter, setFilter] = useState<"all" | "errors">("all")

  const filteredLogs = filter === "all" 
    ? logs 
    : logs.filter(log => log.status === "error" || log.status === "warning")

  const handleExport = () => {
    console.log("Exporting logs...")
  }

  return (
    <Card className="flex flex-col h-full" data-testid={testId}>
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-medium">{title}</h3>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setFilter(filter === "all" ? "errors" : "all")}
            data-testid="button-filter-logs"
          >
            <Filter className="h-4 w-4 mr-2" />
            {filter === "all" ? "Show Errors Only" : "Show All"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleExport}
            data-testid="button-export-logs"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3 font-mono text-sm">
          {filteredLogs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No log entries</p>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className="flex gap-3 p-3 rounded-md bg-muted/50"
                data-testid={`log-entry-${log.id}`}
              >
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {log.timestamp}
                </span>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={log.status} />
                    <span className="text-sm">{log.action}</span>
                  </div>
                  {log.details && (
                    <p className="text-xs text-muted-foreground">{log.details}</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </Card>
  )
}
