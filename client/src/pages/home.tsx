import { StatCard } from "@/components/stat-card";
import { TaskCard } from "@/components/task-card";
import { WorkflowCard } from "@/components/workflow-card";
import { CreateTaskDialog } from "@/components/create-task-dialog";
import { CheckCircle, Clock, Globe, GitBranch, Sparkles, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import heroImage from "@assets/stock_images/modern_browser_autom_8471ea05.jpg";

export default function Home() {
  // todo: remove mock data
  const recentTasks = [
    {
      id: "task-1",
      title: "Send LinkedIn Connection",
      description: "Connect with professionals based on search criteria",
      website: "linkedin.com",
      lastRun: "2 hours ago",
      runCount: 15,
      status: "active" as const,
    },
    {
      id: "task-2",
      title: "Scrape Product Prices",
      description: "Extract pricing data from e-commerce sites",
      website: "amazon.com",
      lastRun: "1 day ago",
      runCount: 42,
      status: "active" as const,
    },
  ];

  const recentWorkflows = [
    {
      id: "workflow-1",
      title: "Lead Generation Pipeline",
      description: "Find prospects, send connections, follow up",
      tasks: ["Search LinkedIn", "Send Connection", "Send Message", "Log to CRM"],
      lastRun: "1 hour ago",
      runCount: 28,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-8 md:p-12">
        <div className="grid gap-8 md:grid-cols-2 items-center">
          <div>
            <h1 className="text-4xl font-bold mb-4">
              Intelligent Browser Automation
            </h1>
            <p className="text-lg text-muted-foreground mb-6">
              Teach AI to automate any website. Create tasks once, run them infinitely.
              Powered by GPT-4, Claude, and Gemini.
            </p>
            <div className="flex gap-3">
              <CreateTaskDialog />
              <Link href="/learn">
                <Button variant="outline" data-testid="button-learn-website">
                  <Sparkles className="h-4 w-4 mr-2" />
                  Learn a Website
                </Button>
              </Link>
            </div>
          </div>
          <div className="flex justify-center">
            <img
              src={heroImage}
              alt="Browser automation illustration"
              className="rounded-lg max-w-full h-auto"
            />
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
          icon={Globe}
        />
        <StatCard
          title="Workflows"
          value={5}
          description="3 running"
          icon={GitBranch}
        />
        <StatCard
          title="Executions Today"
          value={156}
          description="+23 from yesterday"
          icon={TrendingUp}
          trend={{ value: "18%", positive: true }}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Recent Tasks</h2>
            <Link href="/tasks">
              <Button variant="ghost" size="sm" data-testid="link-view-all-tasks">
                View All
              </Button>
            </Link>
          </div>
          <div className="space-y-4">
            {recentTasks.map((task) => (
              <TaskCard
                key={task.id}
                {...task}
                onRun={() => console.log("Run task", task.id)}
                onEdit={() => console.log("Edit task", task.id)}
                onDelete={() => console.log("Delete task", task.id)}
              />
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Active Workflows</h2>
            <Link href="/workflows">
              <Button variant="ghost" size="sm" data-testid="link-view-all-workflows">
                View All
              </Button>
            </Link>
          </div>
          <div className="space-y-4">
            {recentWorkflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                {...workflow}
                onRun={() => console.log("Run workflow", workflow.id)}
                onEdit={() => console.log("Edit workflow", workflow.id)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with common automation tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            <Link href="/learn">
              <Button variant="outline" className="w-full justify-start" data-testid="quick-action-learn">
                <Sparkles className="h-4 w-4 mr-2" />
                Learn New Website
              </Button>
            </Link>
            <Link href="/execute">
              <Button variant="outline" className="w-full justify-start" data-testid="quick-action-run">
                <Clock className="h-4 w-4 mr-2" />
                Run Task Now
              </Button>
            </Link>
            <Link href="/workflows">
              <Button variant="outline" className="w-full justify-start" data-testid="quick-action-workflow">
                <GitBranch className="h-4 w-4 mr-2" />
                Create Workflow
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
