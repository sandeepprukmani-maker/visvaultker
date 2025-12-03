import { Button } from "@/components/ui/button";
import { Zap, ArrowRight } from "lucide-react";

interface EmptyStateProps {
  onGetStarted: () => void;
}

export function EmptyState({ onGetStarted }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="relative">
        <div className="absolute -inset-4 rounded-full bg-gradient-to-r from-purple-500/20 to-blue-500/20 blur-xl" />
        <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500">
          <Zap className="h-10 w-10 text-white" />
        </div>
      </div>
      
      <h2 className="mt-6 text-2xl font-semibold tracking-tight">
        Ready to automate?
      </h2>
      <p className="mt-2 max-w-md text-muted-foreground">
        Describe what you want to automate in plain English, and Eko will create 
        and execute a multi-step workflow for you.
      </p>
      
      <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row">
        <Button
          onClick={onGetStarted}
          className="bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600"
          data-testid="button-get-started"
        >
          Get Started
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      <div className="mt-12 grid gap-4 sm:grid-cols-3">
        {[
          {
            title: "Natural Language",
            description: "Describe tasks in plain English",
          },
          {
            title: "Multi-Step Workflows",
            description: "Complex automations made simple",
          },
          {
            title: "Real-time Execution",
            description: "Watch your automation run live",
          },
        ].map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border bg-card p-4 text-center"
          >
            <h3 className="font-medium">{feature.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
