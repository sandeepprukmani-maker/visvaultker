import { clsx } from "clsx";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const variants: Record<string, { icon: any, style: string, label: string }> = {
    pending: {
      icon: Clock,
      style: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
      label: "Pending"
    },
    running: {
      icon: Loader2,
      style: "bg-blue-500/10 text-blue-500 border-blue-500/20",
      label: "Running"
    },
    completed: {
      icon: CheckCircle2,
      style: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
      label: "Success"
    },
    failed: {
      icon: XCircle,
      style: "bg-red-500/10 text-red-500 border-red-500/20",
      label: "Failed"
    }
  };

  const config = variants[status] || variants.pending;
  const Icon = config.icon;

  return (
    <span className={clsx(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
      config.style,
      className
    )}>
      <Icon className={clsx("w-3.5 h-3.5", status === "running" && "animate-spin")} />
      {config.label}
    </span>
  );
}
