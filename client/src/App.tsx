import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AppSidebar } from "@/components/app-sidebar";
import { TopToolbar } from "@/components/TopToolbar";
import { StatusBar } from "@/components/StatusBar";
import { useState } from "react";

import Dashboard from "@/pages/Dashboard";
import Tasks from "@/pages/Tasks";
import Workflows from "@/pages/Workflows";
import Recordings from "@/pages/Recordings";
import Settings from "@/pages/Settings";
import VoiceStudio from "@/pages/VoiceStudio";
import History from "@/pages/History";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/voice-studio" component={VoiceStudio} />
      <Route path="/tasks" component={Tasks} />
      <Route path="/workflows" component={Workflows} />
      <Route path="/recordings" component={Recordings} />
      <Route path="/history" component={History} />
      <Route path="/settings" component={Settings} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const style = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3rem",
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <SidebarProvider style={style as React.CSSProperties}>
            <div className="flex h-screen w-full">
              <AppSidebar />
              <div className="flex flex-col flex-1">
                <TopToolbar
                  isRunning={isRunning}
                  isRecording={isRecording}
                  onRun={() => setIsRunning(true)}
                  onStop={() => setIsRunning(false)}
                  onRecord={() => setIsRecording(!isRecording)}
                />
                <main className="flex-1 overflow-hidden">
                  <Router />
                </main>
                <StatusBar
                  connectionStatus="connected"
                  browserVersion="Chromium 131.0"
                  executionTime={isRunning ? "Running..." : undefined}
                />
              </div>
            </div>
          </SidebarProvider>
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
