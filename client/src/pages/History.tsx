import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, RotateCcw, AlertCircle, Check, X, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import type { AutomationHistory } from "@shared/schema";
import { useLocation } from "wouter";

export default function History() {
  const { toast } = useToast();
  const [, setLocation] = useLocation();
  const [selectedHistory, setSelectedHistory] = useState<AutomationHistory | null>(null);

  const { data, isLoading } = useQuery<{ success: boolean; history: AutomationHistory[] }>({
    queryKey: ["/api/history"],
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return await apiRequest("DELETE", `/api/history/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/history"] });
      toast({
        title: "Deleted successfully",
        description: "History item has been removed",
      });
    },
    onError: () => {
      toast({
        title: "Delete failed",
        description: "Failed to delete history item",
        variant: "destructive",
      });
    },
  });

  const deleteAllMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest("DELETE", "/api/history");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/history"] });
      toast({
        title: "All history cleared",
        description: "All history items have been removed",
      });
    },
    onError: () => {
      toast({
        title: "Clear all failed",
        description: "Failed to clear all history",
        variant: "destructive",
      });
    },
  });

  const reexecuteMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await apiRequest("POST", `/api/history/${id}/reexecute`);
      return response.json();
    },
    onSuccess: (data) => {
      setLocation("/");
      setTimeout(() => {
        const event = new CustomEvent("reexecute-automation", { detail: data });
        window.dispatchEvent(event);
      }, 100);
      toast({
        title: "Reexecuting automation",
        description: "Redirecting to home page...",
      });
    },
    onError: () => {
      toast({
        title: "Reexecution failed",
        description: "Failed to reexecute automation",
        variant: "destructive",
      });
    },
  });

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(date));
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const history = data?.history || [];

  return (
    <div className="flex h-full gap-4 p-4">
      <div className="flex-1 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Automation History</h1>
          {history.length > 0 && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm" data-testid="button-delete-all">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Clear all history?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete all {history.length} automation history items. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel data-testid="button-cancel-delete-all">Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => deleteAllMutation.mutate()}
                    className="bg-destructive hover:bg-destructive/90"
                    data-testid="button-confirm-delete-all"
                  >
                    Delete All
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>

        {history.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-muted-foreground">No history yet</p>
              <p className="text-sm text-muted-foreground">Your automation history will appear here</p>
            </CardContent>
          </Card>
        ) : (
          <ScrollArea className="flex-1">
            <div className="space-y-4">
              {history.map((item) => (
                <Card
                  key={item.id}
                  className={`cursor-pointer transition-colors hover-elevate ${
                    selectedHistory?.id === item.id ? "ring-2 ring-primary" : ""
                  }`}
                  onClick={() => setSelectedHistory(item)}
                  data-testid={`history-item-${item.id}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base truncate">{item.prompt}</CardTitle>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <Badge variant={item.success ? "default" : "destructive"} className="text-xs">
                            {item.success ? <Check className="h-3 w-3 mr-1" /> : <X className="h-3 w-3 mr-1" />}
                            {item.success ? "Success" : "Failed"}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {item.mode}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(item.createdAt)}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            reexecuteMutation.mutate(item.id);
                          }}
                          disabled={reexecuteMutation.isPending}
                          data-testid={`button-reexecute-${item.id}`}
                        >
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild onClick={(e) => e.stopPropagation()}>
                            <Button
                              size="icon"
                              variant="ghost"
                              data-testid={`button-delete-${item.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete this history item?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel data-testid={`button-cancel-delete-${item.id}`}>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={(e) => {
                                  e.stopPropagation();
                                  deleteMutation.mutate(item.id);
                                  if (selectedHistory?.id === item.id) {
                                    setSelectedHistory(null);
                                  }
                                }}
                                className="bg-destructive hover:bg-destructive/90"
                                data-testid={`button-confirm-delete-${item.id}`}
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </CardHeader>
                  {item.detectedUrl && (
                    <CardContent className="pt-0">
                      <p className="text-sm text-muted-foreground truncate">{item.detectedUrl}</p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>

      <div className="w-96">
        {selectedHistory ? (
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-base">Details</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden">
              {selectedHistory.screenshot && (
                <div>
                  <p className="text-sm font-medium mb-2">Screenshot</p>
                  <img
                    src={selectedHistory.screenshot}
                    alt="Automation screenshot"
                    className="w-full rounded-md border"
                    data-testid={`screenshot-${selectedHistory.id}`}
                  />
                </div>
              )}
              <div>
                <p className="text-sm font-medium mb-2">Execution Logs</p>
                <ScrollArea className="h-64 border rounded-md p-3">
                  <div className="space-y-2">
                    {selectedHistory.logs.map((log) => (
                      <div key={log.id} className="text-xs" data-testid={`log-${log.id}`}>
                        <Badge
                          variant={
                            log.status === "success"
                              ? "default"
                              : log.status === "error"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-xs mb-1"
                        >
                          {log.status}
                        </Badge>
                        <p className="text-muted-foreground">{log.action}</p>
                        {log.description && (
                          <p className="text-muted-foreground mt-1 pl-2 border-l-2">
                            {log.description}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex items-center justify-center">
            <CardContent className="text-center">
              <p className="text-muted-foreground">Select a history item to view details</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
