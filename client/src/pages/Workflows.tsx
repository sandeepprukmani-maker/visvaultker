import { Plus, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Workflows() {
  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Workflows</h2>
          <Button data-testid="button-new-workflow">
            <Plus className="w-4 h-4 mr-2" />
            New Workflow
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <Card className="max-w-md mx-auto mt-16">
          <CardContent className="pt-6 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <GitBranch className="w-8 h-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Visual Workflow Builder</h3>
              <p className="text-sm text-muted-foreground">
                Chain multiple tasks together to create complex automation workflows.
                Use drag-and-drop to connect tasks and define execution order.
              </p>
            </div>
            <Button size="lg" data-testid="button-create-first-workflow">
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Workflow
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
