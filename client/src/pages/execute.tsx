import { BrowserPreview } from "@/components/browser-preview";
import { ExecutionLog } from "@/components/execution-log";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Play, Pause, StopCircle, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useState } from "react";

export default function Execute() {
  const [selectedTask, setSelectedTask] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  // todo: remove mock data
  const logs = [
    { timestamp: "10:23:45", level: "info" as const, message: "Initializing automation task..." },
    { timestamp: "10:23:46", level: "success" as const, message: "Successfully loaded page: https://linkedin.com" },
    { timestamp: "10:23:47", level: "info" as const, message: "AI analyzing page structure..." },
    { timestamp: "10:23:48", level: "success" as const, message: "Located search input element" },
    { timestamp: "10:23:49", level: "loading" as const, message: "Typing search query: 'Software Engineer'" },
    { timestamp: "10:23:51", level: "success" as const, message: "Search completed, processing results..." },
  ];

  const handleRun = () => {
    console.log("Starting execution");
    setIsRunning(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const handlePause = () => {
    console.log("Pausing execution");
    setIsRunning(false);
  };

  const handleStop = () => {
    console.log("Stopping execution");
    setIsRunning(false);
    setProgress(0);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Execute Automation</h1>
        <p className="text-muted-foreground mt-1">
          Run tasks and workflows with real-time monitoring
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Controls</CardTitle>
          <CardDescription>Select and run your automation tasks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Select value={selectedTask} onValueChange={setSelectedTask}>
              <SelectTrigger className="flex-1" data-testid="select-task">
                <SelectValue placeholder="Select a task or workflow" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="task-1">Send LinkedIn Connection</SelectItem>
                <SelectItem value="task-2">Scrape Product Prices</SelectItem>
                <SelectItem value="workflow-1">Lead Generation Pipeline</SelectItem>
                <SelectItem value="workflow-2">Price Monitoring</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                onClick={handleRun}
                disabled={!selectedTask || isRunning}
                data-testid="button-run"
              >
                <Play className="h-4 w-4 mr-2" />
                Run
              </Button>
              <Button
                variant="outline"
                onClick={handlePause}
                disabled={!isRunning}
                data-testid="button-pause"
              >
                <Pause className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                onClick={handleStop}
                disabled={!isRunning && progress === 0}
                data-testid="button-stop"
              >
                <StopCircle className="h-4 w-4" />
              </Button>
              <Button variant="outline" data-testid="button-reset">
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Progress */}
          {progress > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Progress</span>
                <Badge variant={isRunning ? "default" : "secondary"}>
                  {isRunning ? "Running" : "Paused"}
                </Badge>
              </div>
              <Progress value={progress} />
              <p className="text-xs text-muted-foreground">{progress}% complete</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Split View */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr,1fr]">
        {/* Browser Preview */}
        <div className="h-[600px]">
          <BrowserPreview
            url="https://linkedin.com/search/results"
            isLoading={isRunning}
          />
        </div>

        {/* Execution Log */}
        <Card className="h-[600px] flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Execution Log</CardTitle>
            <CardDescription>Real-time automation activity</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0 overflow-hidden">
            <ExecutionLog logs={logs} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
