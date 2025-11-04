import { StatCard } from "@/components/stat-card";
import { TaskCard } from "@/components/task-card";
import { WorkflowCard } from "@/components/workflow-card";
import { CreateTaskDialog } from "@/components/create-task-dialog";
import { CheckCircle, Clock, Globe, GitBranch, Sparkles, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import heroImage from "@assets/stock_images/modern_browser_autom_8471ea05.jpg";

export default function Home() {
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["/api/python/api/analytics/overview"],
  });

  const { data: tasks } = useQuery({
    queryKey: ["/api/python/api/tasks"],
  });

  const { data: workflows } = useQuery({
    queryKey: ["/api/python/api/workflows"],
  });

  const recentTasks = tasks?.slice(0, 2) || [];
  const recentWorkflows = workflows?.slice(0, 2) || [];

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
          value={analyticsLoading ? "..." : analytics?.totalTasks || 0}
          description={`${analytics?.activeTasks || 0} active`}
          icon={CheckCircle}
        />
        <StatCard
          title="Websites Learned"
          value={analyticsLoading ? "..." : analytics?.websitesLearned || 0}
          description="LinkedIn, Twitter, etc."
          icon={Globe}
        />
        <StatCard
          title="Workflows"
          value={analyticsLoading ? "..." : analytics?.totalWorkflows || 0}
          description={`${Math.floor((analytics?.totalWorkflows || 0) * 0.6)} running`}
          icon={GitBranch}
        />
        <StatCard
          title="Executions Today"
          value={analyticsLoading ? "..." : analytics?.executionsToday || 0}
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
          {recentTasks.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-muted-foreground">
                No tasks created yet. Create your first task to get started!
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {recentTasks.map((task: any) => (
                <TaskCard
                  key={task.id}
                  id={task.id}
                  title={task.name}
                  description={task.description || "No description"}
                  website={task.website_url}
                  lastRun="Recently"
                  runCount={0}
                  status="active"
                  onRun={() => console.log("Run task", task.id)}
                  onEdit={() => console.log("Edit task", task.id)}
                />
              ))}
            </div>
          )}
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
          {recentWorkflows.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-muted-foreground">
                No workflows created yet. Chain tasks together to create powerful automations!
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {recentWorkflows.map((workflow: any) => (
                <WorkflowCard
                  key={workflow.id}
                  id={workflow.id}
                  title={workflow.name}
                  description={workflow.description || "No description"}
                  tasks={[]}
                  lastRun="Recently"
                  runCount={0}
                  onRun={() => console.log("Run workflow", workflow.id)}
                  onEdit={() => console.log("Edit workflow", workflow.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* CTA Section */}
      <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
        <CardHeader>
          <CardTitle>Get Started with AutomateAI</CardTitle>
          <CardDescription>
            Follow these simple steps to automate your first website
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
                1
              </div>
              <h3 className="font-semibold">Learn a Website</h3>
              <p className="text-sm text-muted-foreground">
                AI explores and understands the website structure
              </p>
            </div>
            <div className="space-y-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
                2
              </div>
              <h3 className="font-semibold">Create a Task</h3>
              <p className="text-sm text-muted-foreground">
                Demonstrate the automation once, AI learns it forever
              </p>
            </div>
            <div className="space-y-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
                3
              </div>
              <h3 className="font-semibold">Run & Scale</h3>
              <p className="text-sm text-muted-foreground">
                Execute tasks individually or chain them into workflows
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
