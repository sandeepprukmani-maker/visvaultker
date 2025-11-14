import { CheckCircle, Copy, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

interface ResultsDisplayProps {
  result: string;
  executedCode: string;
  pageState: string;
  tokensUsed: number;
  executionTime: number;
  onNewAutomation: () => void;
  onSaveToHistory: () => void;
}

export function ResultsDisplay({
  result,
  executedCode,
  pageState,
  tokensUsed,
  executionTime,
  onNewAutomation,
  onSaveToHistory,
}: ResultsDisplayProps) {
  const { toast } = useToast();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      description: "Copied to clipboard",
    });
  };

  return (
    <div className="space-y-6" data-testid="results-display">
      {/* Success Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-600" data-testid="icon-success" />
          <div>
            <h2 className="text-lg font-medium" data-testid="text-result-title">Automation Complete</h2>
            <p className="text-xs text-muted-foreground" data-testid="text-execution-time">
              Completed in {(executionTime / 1000).toFixed(2)}s • {tokensUsed.toLocaleString()} tokens used
            </p>
          </div>
        </div>
      </div>

      {/* Executed Code Section */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium">Playwright Code Executed</CardTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => copyToClipboard(executedCode)}
              className="h-8 w-8"
              data-testid="button-copy-code"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-lg bg-muted text-sm font-mono overflow-x-auto" data-testid="code-executed">
            <code>{executedCode}</code>
          </pre>
        </CardContent>
      </Card>

      {/* Page State Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">Current Page State</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-lg bg-muted text-sm font-mono overflow-x-auto whitespace-pre-wrap" data-testid="text-page-state">
            {pageState}
          </pre>
        </CardContent>
      </Card>

      {/* Result Message */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">Result</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm" data-testid="text-result-message">{result}</p>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-4 pt-4">
        <Button 
          variant="outline"
          onClick={onSaveToHistory}
          data-testid="button-save-history"
        >
          Save to History
        </Button>
        <Button 
          onClick={onNewAutomation}
          data-testid="button-new-automation-results"
        >
          New Automation
        </Button>
      </div>
    </div>
  );
}
