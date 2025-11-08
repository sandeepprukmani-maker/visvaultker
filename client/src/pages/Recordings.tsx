import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Circle, Square, Save, Play, ArrowLeft, RefreshCw, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Recording } from "@shared/schema";

interface BrowserAction {
  type: 'click' | 'input' | 'navigate' | 'keypress';
  selector?: string;
  value?: string;
  url?: string;
  key?: string;
  timestamp: number;
}

export default function Recordings() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingName, setRecordingName] = useState("");
  const [actions, setActions] = useState<BrowserAction[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [currentUrl, setCurrentUrl] = useState("https://www.google.com");
  const [urlInput, setUrlInput] = useState("https://www.google.com");
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { toast } = useToast();

  const createRecording = useMutation({
    mutationFn: async (data: { name: string; actions: any[] }) => {
      const res = await apiRequest('POST', '/api/recordings', data);
      return res.json();
    },
    onSuccess: async (recording) => {
      await queryClient.invalidateQueries({ queryKey: ['/api/recordings'] });
      
      const res = await apiRequest('POST', `/api/recordings/${recording.id}/generate-code`);
      const updated = await res.json();
      
      await queryClient.invalidateQueries({ queryKey: ['/api/recordings'] });
      
      await apiRequest('POST', `/api/recordings/${recording.id}/save-as-task`);
      await queryClient.invalidateQueries({ queryKey: ['/api/tasks'] });
      
      setSaveDialogOpen(false);
      setRecordingName("");
      setActions([]);
      setIsRecording(false);
      toast({
        title: "Success!",
        description: "Recording saved and task created",
      });
    },
  });

  useEffect(() => {
    if (isRecording && iframeRef.current?.contentWindow) {
      const iframe = iframeRef.current;
      
      const handleMessage = (event: MessageEvent) => {
        if (event.source !== iframe.contentWindow) return;
        
        if (event.data.type === 'action') {
          const action: BrowserAction = {
            ...event.data.action,
            timestamp: Date.now(),
          };
          setActions(prev => [...prev, action]);
        }
      };
      
      window.addEventListener('message', handleMessage);
      
      try {
        iframe.contentWindow?.postMessage({ type: 'startRecording' }, '*');
      } catch (e) {
        console.error('Could not communicate with iframe:', e);
      }
      
      return () => {
        window.removeEventListener('message', handleMessage);
        try {
          iframe.contentWindow?.postMessage({ type: 'stopRecording' }, '*');
        } catch (e) {
          console.error('Could not stop recording:', e);
        }
      };
    }
  }, [isRecording]);

  const handleStartRecording = () => {
    setActions([]);
    setIsRecording(true);
    toast({
      title: "Recording started",
      description: "All actions in the browser will be captured",
    });
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    
    if (actions.length === 0) {
      toast({
        title: "No actions recorded",
        description: "Perform some actions before stopping",
        variant: "destructive",
      });
      return;
    }
    
    setSaveDialogOpen(true);
  };

  const handleSaveRecording = () => {
    if (recordingName.trim() && actions.length > 0) {
      createRecording.mutate({
        name: recordingName.trim(),
        actions: actions,
      });
    }
  };

  const handleNavigate = () => {
    if (urlInput.trim()) {
      const action: BrowserAction = {
        type: 'navigate',
        url: urlInput,
        timestamp: Date.now(),
      };
      if (isRecording) {
        setActions(prev => [...prev, action]);
      }
      setCurrentUrl(urlInput);
      if (iframeRef.current?.contentWindow) {
        iframeRef.current.contentWindow.postMessage({ type: 'navigate', url: urlInput }, '*');
      }
    }
  };

  const handleRefresh = () => {
    if (iframeRef.current) {
      iframeRef.current.src = currentUrl;
    }
  };

  const handleBack = () => {
    if (iframeRef.current?.contentWindow) {
      try {
        iframeRef.current.contentWindow.history.back();
      } catch (e) {
        console.error('Could not go back:', e);
      }
    }
  };

  const generatePlaywrightCode = () => {
    let code = `import { test, expect } from '@playwright/test';\n\n`;
    code += `test('${recordingName || 'recorded test'}', async ({ page }) => {\n`;
    
    actions.forEach((action) => {
      if (action.type === 'navigate' && action.url) {
        code += `  await page.goto('${action.url}');\n`;
      } else if (action.type === 'click' && action.selector) {
        code += `  await page.click('${action.selector}');\n`;
      } else if (action.type === 'input' && action.selector && action.value) {
        code += `  await page.fill('${action.selector}', '${action.value}');\n`;
      } else if (action.type === 'keypress' && action.key) {
        code += `  await page.keyboard.press('${action.key}');\n`;
      }
    });
    
    code += `});\n`;
    return code;
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <div className="p-4 border-b border-border bg-background">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div>
            <h1 className="text-2xl font-bold">Browser Recording</h1>
            <p className="text-sm text-muted-foreground">
              Interact with websites and record your actions as Playwright code
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isRecording && (
              <Badge variant="destructive" className="gap-2">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                Recording ({actions.length} actions)
              </Badge>
            )}
            <Button
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              variant={isRecording ? "destructive" : "default"}
              data-testid="button-toggle-recording"
            >
              {isRecording ? (
                <>
                  <Square className="w-4 h-4 mr-2" />
                  Stop & Save
                </>
              ) : (
                <>
                  <Circle className="w-4 h-4 mr-2" />
                  Start Recording
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="outline"
            onClick={handleBack}
            data-testid="button-back"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <Button
            size="icon"
            variant="outline"
            onClick={handleRefresh}
            data-testid="button-refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Input
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleNavigate()}
            placeholder="Enter URL..."
            className="flex-1"
            data-testid="input-url"
          />
          <Button onClick={handleNavigate} data-testid="button-navigate">
            Go
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden p-4 bg-muted/30">
        <Card className="h-full overflow-hidden">
          <CardContent className="p-0 h-full">
            <iframe
              ref={iframeRef}
              src="/recorder-proxy.html"
              className="w-full h-full border-0"
              title="Browser Window"
              sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-top-navigation"
              data-testid="iframe-browser"
            />
          </CardContent>
        </Card>
      </div>

      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Save Recording</DialogTitle>
            <DialogDescription>
              Give your recording a name. It will be saved and converted to a Playwright task.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Recording Name</label>
              <Input
                placeholder="e.g., Login Flow, Search Products"
                value={recordingName}
                onChange={(e) => setRecordingName(e.target.value)}
                data-testid="input-recording-name"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">
                Captured Actions ({actions.length})
              </label>
              <div className="max-h-[200px] overflow-y-auto border rounded-md p-3 bg-muted/50 space-y-1">
                {actions.map((action, idx) => (
                  <div key={idx} className="text-xs font-mono flex items-start gap-2">
                    <Badge variant="outline" className="text-xs">
                      {action.type}
                    </Badge>
                    <span className="text-muted-foreground flex-1 truncate">
                      {action.url || action.selector || action.value || action.key}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Generated Playwright Code Preview</label>
              <pre className="max-h-[250px] overflow-auto border rounded-md p-3 bg-muted text-xs">
                {generatePlaywrightCode()}
              </pre>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSaveRecording}
                disabled={!recordingName.trim() || createRecording.isPending}
                data-testid="button-save-recording"
              >
                {createRecording.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save as Task
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
