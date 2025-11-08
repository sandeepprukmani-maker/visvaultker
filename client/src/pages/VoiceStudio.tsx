import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Mic, MicOff, Code, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { VoiceRequest } from "@shared/schema";

export default function VoiceStudio() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [selectedRequest, setSelectedRequest] = useState<VoiceRequest | null>(null);
  const { toast } = useToast();

  const { data: voiceRequests = [], isLoading } = useQuery<VoiceRequest[]>({
    queryKey: ['/api/voice-requests'],
  });

  const createVoiceRequest = useMutation({
    mutationFn: async (data: { transcript: string; language: string }) => {
      const res = await apiRequest('POST', '/api/voice-requests', data);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/voice-requests'] });
      toast({
        title: "Voice request created",
        description: "Your transcript has been saved",
      });
    },
  });

  const generateCode = useMutation({
    mutationFn: async (id: string) => {
      const res = await apiRequest('POST', `/api/voice-requests/${id}/generate`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/voice-requests'] });
      toast({
        title: "Code generated",
        description: "Your code has been created from the voice request",
      });
    },
  });

  const handleStartRecording = () => {
    setIsRecording(true);
    setTranscript("");
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(prev => prev + finalTranscript + interimTranscript);
      };

      recognition.onerror = () => {
        setIsRecording(false);
        toast({
          title: "Recording error",
          description: "Could not access microphone",
          variant: "destructive",
        });
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
      (window as any).currentRecognition = recognition;
    } else {
      toast({
        title: "Not supported",
        description: "Speech recognition is not supported in your browser",
        variant: "destructive",
      });
      setIsRecording(false);
    }
  };

  const handleStopRecording = () => {
    if ((window as any).currentRecognition) {
      (window as any).currentRecognition.stop();
    }
    setIsRecording(false);
  };

  const handleSaveTranscript = () => {
    if (transcript.trim()) {
      createVoiceRequest.mutate({
        transcript: transcript.trim(),
        language: "typescript",
      });
      setTranscript("");
    }
  };

  const handleGenerateCode = (request: VoiceRequest) => {
    generateCode.mutate(request.id);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen overflow-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Voice Studio</h1>
        <p className="text-muted-foreground">Create code from your voice commands</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Voice Input</CardTitle>
            <CardDescription>Speak your coding request or type it manually</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                variant={isRecording ? "destructive" : "default"}
                data-testid="button-record"
                className="flex-1"
              >
                {isRecording ? (
                  <>
                    <MicOff className="w-4 h-4 mr-2" />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4 mr-2" />
                    Start Recording
                  </>
                )}
              </Button>
            </div>

            <Textarea
              placeholder="Transcript will appear here or type manually..."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="min-h-[200px]"
              data-testid="input-transcript"
            />

            <Button
              onClick={handleSaveTranscript}
              disabled={!transcript.trim() || createVoiceRequest.isPending}
              className="w-full"
              data-testid="button-save"
            >
              {createVoiceRequest.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Request
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Requests</CardTitle>
            <CardDescription>Your voice-to-code history</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="w-8 h-8 animate-spin" data-testid="loader-requests" />
              </div>
            ) : voiceRequests.length === 0 ? (
              <p className="text-center text-muted-foreground p-8" data-testid="text-no-requests">
                No voice requests yet. Start by recording or typing a request!
              </p>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {voiceRequests.map((request) => (
                  <Card key={request.id} className="hover-elevate" data-testid={`card-request-${request.id}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium line-clamp-2" data-testid={`text-transcript-${request.id}`}>
                            {request.transcript}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" data-testid={`badge-status-${request.id}`}>
                              {getStatusIcon(request.status)}
                              <span className="ml-1">{request.status}</span>
                            </Badge>
                            {request.language && (
                              <Badge variant="outline">{request.language}</Badge>
                            )}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleGenerateCode(request)}
                          disabled={!request.transcript || generateCode.isPending || request.status === 'completed'}
                          data-testid={`button-generate-${request.id}`}
                        >
                          <Code className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
