import { CheckCircle2, Circle, AlertCircle, XCircle, Clock, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export type Status = "success" | "running" | "warning" | "error" | "queued" | "idle"

interface StatusBadgeProps {
  status: Status
  label?: string
  className?: string
  testId?: string
}

const statusConfig = {
  success: {
    icon: CheckCircle2,
    className: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    label: "Success",
    animate: false,
  },
  running: {
    icon: Loader2,
    className: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
    label: "Running",
    animate: true,
  },
  warning: {
    icon: AlertCircle,
    className: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20",
    label: "Warning",
    animate: false,
  },
  error: {
    icon: XCircle,
    className: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    label: "Error",
    animate: false,
  },
  queued: {
    icon: Clock,
    className: "bg-muted text-muted-foreground border-border",
    label: "Queued",
    animate: false,
  },
  idle: {
    icon: Circle,
    className: "bg-muted text-muted-foreground border-border",
    label: "Idle",
    animate: false,
  },
}

export function StatusBadge({ status, label, className, testId }: StatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Badge
      variant="outline"
      className={cn("gap-1.5 font-medium", config.className, className)}
      data-testid={testId || `status-${status}`}
    >
      <Icon className={cn("h-3 w-3", config.animate && "animate-spin")} />
      {label || config.label}
    </Badge>
  )
}
