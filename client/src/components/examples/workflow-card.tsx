import { WorkflowCard } from "../workflow-card";

export default function WorkflowCardExample() {
  return (
    <div className="grid gap-4 md:grid-cols-2 p-4">
      <WorkflowCard
        id="workflow-1"
        title="Lead Generation Pipeline"
        description="Find prospects, send connections, follow up"
        tasks={["Search LinkedIn", "Send Connection", "Send Message", "Log to CRM"]}
        lastRun="1 hour ago"
        runCount={28}
        onRun={() => console.log("Run workflow")}
        onEdit={() => console.log("Edit workflow")}
      />
      <WorkflowCard
        id="workflow-2"
        title="Price Monitoring"
        description="Track competitor pricing and update spreadsheet"
        tasks={["Scrape Prices", "Compare Data", "Export CSV"]}
        lastRun="6 hours ago"
        runCount={156}
        onRun={() => console.log("Run workflow")}
        onEdit={() => console.log("Edit workflow")}
      />
    </div>
  );
}
