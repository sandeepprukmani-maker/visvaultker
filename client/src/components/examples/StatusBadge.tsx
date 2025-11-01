import { StatusBadge } from "../status-badge"

export default function StatusBadgeExample() {
  return (
    <div className="p-6 flex flex-wrap gap-3">
      <StatusBadge status="success" />
      <StatusBadge status="running" />
      <StatusBadge status="warning" />
      <StatusBadge status="error" />
      <StatusBadge status="queued" />
      <StatusBadge status="idle" />
    </div>
  )
}
