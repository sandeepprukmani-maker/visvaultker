import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Loader2, 
  Play, 
  Video,
  FileCode,
  Calendar
} from "lucide-react";
import { format } from "date-fns";
import type { Execution } from "@shared/schema";

export default function History() {
  const [selectedType, setSelectedType] = useState<'all' | 'execution' | 'recording'>('all');
  const [selectedItem, setSelectedItem] = useState<any | null>(null);

  const { data: history = [], isLoading } = useQuery<any[]>({
    queryKey: ['/api/history', selectedType],
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any; color: string }> = {
      completed: { variant: 'default', icon: CheckCircle2, color: 'text-green-500' },
      failed: { variant: 'destructive', icon: XCircle, color: 'text-red-500' },
      running: { variant: 'secondary', icon: Loader2, color: 'text-blue-500' },
      pending: { variant: 'outline', icon: Clock, color: 'text-yellow-500' },
    };

    const config = variants[status] || variants.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} data-testid={`badge-status-${status}`}>
        <Icon className={`w-3 h-3 mr-1 ${config.color} ${status === 'running' ? 'animate-spin' : ''}`} />
        {status}
      </Badge>
    );
  };

  const getTypeIcon = (type: string) => {
    return type === 'execution' ? (
      <Play className="w-4 h-4 text-primary" />
    ) : (
      <Video className="w-4 h-4 text-primary" />
    );
  };

  return (
    <div className="h-screen overflow-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">History</h1>
        <p className="text-muted-foreground">View all executions and recordings</p>
      </div>

      <Tabs value={selectedType} onValueChange={(v) => setSelectedType(v as any)} className="w-full">
        <TabsList data-testid="tabs-history-type">
          <TabsTrigger value="all" data-testid="tab-all">All</TabsTrigger>
          <TabsTrigger value="execution" data-testid="tab-executions">Executions</TabsTrigger>
          <TabsTrigger value="recording" data-testid="tab-recordings">Recordings</TabsTrigger>
        </TabsList>

        <TabsContent value={selectedType} className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>History Items</CardTitle>
                  <CardDescription>
                    {selectedType === 'all' ? 'All history items' : 
                     selectedType === 'execution' ? 'Script execution history' : 
                     'Recording history'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="flex justify-center p-8">
                      <Loader2 className="w-8 h-8 animate-spin" data-testid="loader-history" />
                    </div>
                  ) : history.length === 0 ? (
                    <p className="text-center text-muted-foreground p-8" data-testid="text-no-history">
                      No history items yet. Start by running scripts or creating recordings!
                    </p>
                  ) : (
                    <ScrollArea className="h-[600px]">
                      <div className="space-y-3">
                        {history.map((item) => (
                          <Card
                            key={item.id}
                            className="hover-elevate cursor-pointer"
                            onClick={() => setSelectedItem(item)}
                            data-testid={`card-history-${item.id}`}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-start gap-3 flex-1 min-w-0">
                                  <div className="mt-1">
                                    {getTypeIcon(item.type)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="font-medium line-clamp-1" data-testid={`text-name-${item.id}`}>
                                      {item.taskName || item.name || 'Untitled'}
                                    </p>
                                    <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
                                      <Calendar className="w-3 h-3" />
                                      {format(new Date(item.startedAt || item.createdAt), 'PPp')}
                                    </p>
                                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                                      {getStatusBadge(item.status)}
                                      {item.duration && (
                                        <Badge variant="outline">
                                          <Clock className="w-3 h-3 mr-1" />
                                          {item.duration}ms
                                        </Badge>
                                      )}
                                      <Badge variant="secondary">
                                        {item.type}
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </div>

            <div>
              <Card>
                <CardHeader>
                  <CardTitle>Details</CardTitle>
                  <CardDescription>Selected item information</CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedItem ? (
                    <div className="space-y-4" data-testid="details-panel">
                      <div>
                        <h3 className="font-semibold mb-2">Status</h3>
                        {getStatusBadge(selectedItem.status)}
                      </div>

                      <Separator />

                      <div>
                        <h3 className="font-semibold mb-2">Type</h3>
                        <Badge variant="secondary">{selectedItem.type}</Badge>
                      </div>

                      {selectedItem.duration && (
                        <>
                          <Separator />
                          <div>
                            <h3 className="font-semibold mb-2">Duration</h3>
                            <p className="text-sm">{selectedItem.duration}ms</p>
                          </div>
                        </>
                      )}

                      {selectedItem.logs && (
                        <>
                          <Separator />
                          <div>
                            <h3 className="font-semibold mb-2 flex items-center gap-2">
                              <FileCode className="w-4 h-4" />
                              Logs
                            </h3>
                            <ScrollArea className="h-[200px]">
                              <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                                {selectedItem.logs}
                              </pre>
                            </ScrollArea>
                          </div>
                        </>
                      )}

                      {selectedItem.error && (
                        <>
                          <Separator />
                          <div>
                            <h3 className="font-semibold mb-2 text-destructive">Error</h3>
                            <p className="text-sm bg-destructive/10 p-3 rounded-md">
                              {selectedItem.error}
                            </p>
                          </div>
                        </>
                      )}

                      {selectedItem.generatedCode && (
                        <>
                          <Separator />
                          <div>
                            <h3 className="font-semibold mb-2">Generated Code</h3>
                            <ScrollArea className="h-[200px]">
                              <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                                {selectedItem.generatedCode}
                              </pre>
                            </ScrollArea>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground p-8">
                      Select an item to view details
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
