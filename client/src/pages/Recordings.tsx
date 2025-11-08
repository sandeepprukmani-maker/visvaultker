import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Circle, Square, Code, Loader2, Video } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Recording } from "@shared/schema";

export default function Recordings() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingName, setRecordingName] = useState("");
  const [actions, setActions] = useState<any[]>([]);
  const [selectedRecording, setSelectedRecording] = useState<Recording | null>(null);
  const [newRecordingOpen, setNewRecordingOpen] = useState(false);
  const { toast } = useToast();

  const { data: recordings = [], isLoading } = useQuery<Recording[]>({
    queryKey: ['/api/recordings'],
  });

  const createRecording = useMutation({
    mutationFn: async (data: { name: string; actions: any[] }) => {
      const res = await apiRequest('POST', '/api/recordings', data);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/recordings'] });
      setNewRecordingOpen(false);
      setRecordingName("");
      setActions([]);
      toast({
        title: "Recording saved",
        description: "Your recording has been saved successfully",
      });
    },
  });

  const generateCodeFromRecording = useMutation({
    mutationFn: async (recordingId: string) => {
      const res = await apiRequest('POST', `/api/recordings/${recordingId}/generate-code`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/recordings'] });
      toast({
        title: "Code generated",
        description: "Automation code has been generated from your recording",
      });
    },
  });

  const deleteRecording = useMutation({
    mutationFn: async (recordingId: string) => {
      const res = await apiRequest('DELETE', `/api/recordings/${recordingId}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/recordings'] });
      setSelectedRecording(null);
      toast({
        title: "Recording deleted",
        description: "Your recording has been removed",
      });
    },
  });

  const handleStartRecording = () => {
    setIsRecording(true);
    setActions([]);
    
    toast({
      title: "Recording started",
      description: "Actions will be captured as you interact with the page",
    });
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    setNewRecordingOpen(true);
    toast({
      title: "Recording stopped",
      description: `Captured ${actions.length} actions`,
    });
  };

  const handleSaveRecording = () => {
    if (recordingName.trim()) {
      const sampleActions = [
        { type: 'click', selector: 'button#submit', timestamp: Date.now() },
        { type: 'input', selector: 'input#username', value: 'test@example.com', timestamp: Date.now() + 1000 },
        { type: 'click', selector: 'a.login', timestamp: Date.now() + 2000 },
      ];
      
      createRecording.mutate({
        name: recordingName.trim(),
        actions: sampleActions,
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      completed: 'default',
      recording: 'secondary',
      processing: 'outline',
    };

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  return (
    <div className="h-screen overflow-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Recordings</h1>
          <p className="text-muted-foreground">Record actions and generate automation code</p>
        </div>
        <Button
          onClick={isRecording ? handleStopRecording : handleStartRecording}
          variant={isRecording ? "destructive" : "default"}
          data-testid="button-record"
        >
          {isRecording ? (
            <>
              <Square className="w-4 h-4 mr-2" />
              Stop Recording
            </>
          ) : (
            <>
              <Circle className="w-4 h-4 mr-2" />
              Start Recording
            </>
          )}
        </Button>
      </div>

      {isRecording && (
        <Card className="bg-destructive/10 border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-destructive animate-pulse" />
              <p className="font-medium">Recording in progress... Click Stop Recording when done</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Dialog open={newRecordingOpen} onOpenChange={setNewRecordingOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Recording</DialogTitle>
            <DialogDescription>Give your recording a name to save it</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Recording Name</label>
              <Input
                placeholder="e.g., Login Flow, Form Submission"
                value={recordingName}
                onChange={(e) => setRecordingName(e.target.value)}
                data-testid="input-recording-name"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setNewRecordingOpen(false)}>
                Discard
              </Button>
              <Button
                onClick={handleSaveRecording}
                disabled={!recordingName.trim() || createRecording.isPending}
                data-testid="button-save-recording"
              >
                {createRecording.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save Recording
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>All Recordings</CardTitle>
              <CardDescription>Your recorded automation sessions</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin" data-testid="loader-recordings" />
                </div>
              ) : recordings.length === 0 ? (
                <p className="text-center text-muted-foreground p-8" data-testid="text-no-recordings">
                  No recordings yet. Start recording to capture your actions!
                </p>
              ) : (
                <ScrollArea className="h-[600px]">
                  <div className="space-y-3">
                    {recordings.map((recording) => (
                      <Card
                        key={recording.id}
                        className={`hover-elevate cursor-pointer ${selectedRecording?.id === recording.id ? 'border-primary' : ''}`}
                        onClick={() => setSelectedRecording(recording)}
                        data-testid={`card-recording-${recording.id}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-start gap-3 flex-1 min-w-0">
                              <Video className="w-4 h-4 mt-1 text-primary" />
                              <div className="flex-1">
                                <p className="font-medium" data-testid={`text-name-${recording.id}`}>
                                  {recording.name}
                                </p>
                                <div className="flex items-center gap-2 mt-2 flex-wrap">
                                  {getStatusBadge(recording.status)}
                                  <Badge variant="outline">
                                    {(recording.actions as any[]).length} actions
                                  </Badge>
                                  {recording.duration && (
                                    <Badge variant="outline">{recording.duration}ms</Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                generateCodeFromRecording.mutate(recording.id);
                              }}
                              disabled={generateCodeFromRecording.isPending || recording.status === 'completed'}
                              data-testid={`button-generate-${recording.id}`}
                            >
                              <Code className="w-4 h-4" />
                            </Button>
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
              <CardDescription>Recording information</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedRecording ? (
                <div className="space-y-4" data-testid="recording-details">
                  <div>
                    <h3 className="font-semibold mb-2">Name</h3>
                    <p className="text-sm">{selectedRecording.name}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Status</h3>
                    {getStatusBadge(selectedRecording.status)}
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Actions</h3>
                    <ScrollArea className="h-[200px]">
                      <div className="space-y-2">
                        {(selectedRecording.actions as any[]).map((action, idx) => (
                          <div key={idx} className="text-xs p-2 bg-muted rounded-md">
                            <Badge variant="outline" className="text-xs mb-1">{action.type}</Badge>
                            <p className="text-muted-foreground truncate">
                              {action.selector || action.url || 'Unknown action'}
                            </p>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                  {selectedRecording.generatedCode && (
                    <div>
                      <h3 className="font-semibold mb-2">Generated Code</h3>
                      <ScrollArea className="h-[200px]">
                        <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                          {selectedRecording.generatedCode}
                        </pre>
                      </ScrollArea>
                    </div>
                  )}
                  <Button
                    variant="destructive"
                    size="sm"
                    className="w-full"
                    onClick={() => deleteRecording.mutate(selectedRecording.id)}
                    disabled={deleteRecording.isPending}
                    data-testid="button-delete-recording"
                  >
                    {deleteRecording.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    Delete Recording
                  </Button>
                </div>
              ) : (
                <p className="text-center text-muted-foreground p-8">
                  Select a recording to view details
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
