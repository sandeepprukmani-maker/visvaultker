import { WorkflowCard } from "@/components/workflow-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent } from "@/components/ui/card";

export default function Workflows() {
  const [searchQuery, setSearchQuery] = useState("");
  const { toast } = useToast();

  const { data: workflows, isLoading } = useQuery({
    queryKey: ["/api/python/api/workflows"],
  });

  const filteredWorkflows = (workflows || []).filter((workflow: any) => {
    return workflow.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
           workflow.description?.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workflows</h1>
          <p className="text-muted-foreground mt-1">
            Chain multiple tasks into automated workflows
          </p>
        </div>
        <Button 
          onClick={() => toast({ title: "Workflow builder coming soon!" })}
          data-testid="button-create-workflow"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Workflow
        </Button>
      </div>

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

      {isLoading ? (
        <Card>
          <CardContent className="p-6 text-center">
            Loading workflows...
          </CardContent>
        </Card>
      ) : filteredWorkflows.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            No workflows created yet. Create tasks first, then chain them into workflows!
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredWorkflows.map((workflow: any) => (
            <WorkflowCard
              key={workflow.id}
              id={workflow.id}
              title={workflow.name}
              description={workflow.description || "No description"}
              tasks={[]}
              lastRun="Recently"
              runCount={0}
              onRun={() => toast({ title: "Running workflow", description: workflow.name })}
              onEdit={() => toast({ title: "Edit workflow feature coming soon!" })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
