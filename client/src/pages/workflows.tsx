import { WorkflowCard } from "@/components/workflow-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus } from "lucide-react";
import { useState } from "react";

export default function Workflows() {
  const [searchQuery, setSearchQuery] = useState("");

  // todo: remove mock data
  const workflows = [
    {
      id: "workflow-1",
      title: "Lead Generation Pipeline",
      description: "Find prospects, send connections, follow up",
      tasks: ["Search LinkedIn", "Send Connection", "Send Message", "Log to CRM"],
      lastRun: "1 hour ago",
      runCount: 28,
    },
    {
      id: "workflow-2",
      title: "Price Monitoring",
      description: "Track competitor pricing and update spreadsheet",
      tasks: ["Scrape Prices", "Compare Data", "Export CSV"],
      lastRun: "6 hours ago",
      runCount: 156,
    },
    {
      id: "workflow-3",
      title: "Social Media Scheduler",
      description: "Post content across multiple platforms",
      tasks: ["Post to Twitter", "Post to LinkedIn", "Schedule Instagram", "Track Analytics"],
      lastRun: "12 hours ago",
      runCount: 45,
    },
    {
      id: "workflow-4",
      title: "Job Application Automation",
      description: "Find and apply to relevant job postings",
      tasks: ["Search Jobs", "Filter by Criteria", "Auto-Fill Application", "Track Submissions"],
      lastRun: "2 days ago",
      runCount: 12,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workflows</h1>
          <p className="text-muted-foreground mt-1">
            Chain multiple tasks into automated workflows
          </p>
        </div>
        <Button data-testid="button-create-workflow">
          <Plus className="h-4 w-4 mr-2" />
          Create Workflow
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search workflows..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
          data-testid="input-search-workflows"
        />
      </div>

      {/* Workflow Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {workflows.map((workflow) => (
          <WorkflowCard
            key={workflow.id}
            {...workflow}
            onRun={() => console.log("Run workflow", workflow.id)}
            onEdit={() => console.log("Edit workflow", workflow.id)}
          />
        ))}
      </div>
    </div>
  );
}
