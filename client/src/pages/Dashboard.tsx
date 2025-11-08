import { useState } from "react";
import { AIPromptInput } from "@/components/AIPromptInput";
import { BrowserPreview } from "@/components/BrowserPreview";
import { CodeEditor } from "@/components/CodeEditor";
import { ExecutionStatus } from "@/components/ExecutionStatus";
import { RecordingIndicator } from "@/components/RecordingIndicator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Dashboard() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [generatedCode, setGeneratedCode] = useState("");

  // Mock execution steps
  const executionSteps = [
    {
      id: "1",
      action: "Navigate to target URL",
      status: "completed" as const,
      duration: "1.2s",
      timestamp: new Date().toLocaleTimeString(),
    },
    {
      id: "2",
      action: "Wait for page load",
      status: "completed" as const,
      duration: "0.8s",
      timestamp: new Date().toLocaleTimeString(),
    },
    {
      id: "3",
      action: "Extract data from page",
      status: "running" as const,
      timestamp: new Date().toLocaleTimeString(),
    },
  ];

  const handleGenerate = (prompt: string) => {
    setIsGenerating(true);
    // Simulate AI generation
    setTimeout(() => {
      const mockCode = `import { chromium } from 'playwright';

async function automation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // ${prompt}
  await page.goto('https://example.com');
  await page.waitForLoadState('networkidle');
  
  // Take screenshot
  await page.screenshot({ path: 'result.png' });
  
  await browser.close();
}

automation();`;
      setGeneratedCode(mockCode);
      setIsGenerating(false);
    }, 2000);
  };

  const handleRunCode = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 5000);
  };

  return (
    <div className="flex flex-col h-screen">
      <RecordingIndicator isRecording={isRecording} onStop={() => setIsRecording(false)} />
      
      <div className="flex-1 overflow-hidden p-4 space-y-4">
        <div className="bg-card border border-card-border rounded-md p-4">
          <AIPromptInput onGenerate={handleGenerate} isGenerating={isGenerating} />
        </div>

        <div className="grid grid-cols-2 gap-4 h-[calc(100%-200px)]">
          <div className="flex flex-col gap-4">
            <BrowserPreview url="https://example.com" isLoading={isRunning} />
          </div>

          <Tabs defaultValue="code" className="flex flex-col h-full">
            <TabsList className="w-fit">
              <TabsTrigger value="code" data-testid="tab-code">Code</TabsTrigger>
              <TabsTrigger value="execution" data-testid="tab-execution">Execution</TabsTrigger>
            </TabsList>
            <TabsContent value="code" className="flex-1 mt-3">
              <CodeEditor 
                code={generatedCode} 
                language="typescript"
                onRun={handleRunCode}
              />
            </TabsContent>
            <TabsContent value="execution" className="flex-1 mt-3">
              <ExecutionStatus steps={executionSteps} currentStep={2} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
