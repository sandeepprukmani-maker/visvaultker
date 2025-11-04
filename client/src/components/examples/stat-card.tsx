import { CheckCircle } from "lucide-react";
import { StatCard } from "../stat-card";

export default function StatCardExample() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 p-4">
      <StatCard
        title="Total Tasks"
        value={24}
        description="8 active"
        icon={CheckCircle}
        trend={{ value: "12%", positive: true }}
      />
      <StatCard
        title="Websites Learned"
        value={7}
        description="LinkedIn, Twitter, etc."
        icon={CheckCircle}
      />
    </div>
  );
}
