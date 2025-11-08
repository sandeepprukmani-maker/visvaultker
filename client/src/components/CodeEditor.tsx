import { useState, useRef } from "react";
import { Copy, Download, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface CodeEditorProps {
  code?: string;
  language?: string;
  readOnly?: boolean;
  onRun?: () => void;
}

export function CodeEditor({ 
  code = "", 
  language = "javascript",
  readOnly = false,
  onRun 
}: CodeEditorProps) {
  const [currentCode, setCurrentCode] = useState(code);
  const { toast } = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(currentCode);
    toast({
      title: "Copied to clipboard",
      description: "Code has been copied to your clipboard",
    });
  };

  const handleDownload = () => {
    const blob = new Blob([currentCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `automation.${language === 'javascript' ? 'js' : 'ts'}`;
    a.click();
    URL.revokeObjectURL(url);
    toast({
      title: "Downloaded",
      description: "Code has been downloaded",
    });
  };

  return (
    <div className="flex flex-col h-full bg-card border border-card-border rounded-md">
      <div className="flex items-center justify-between p-3 border-b border-card-border">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {language}
          </span>
          <span className="text-xs text-muted-foreground">
            {currentCode.split('\n').length} lines
          </span>
        </div>
        <div className="flex items-center gap-1">
          {onRun && (
            <Button size="sm" variant="default" onClick={onRun} data-testid="button-run-code">
              <Play className="w-3 h-3 mr-1" />
              Run
            </Button>
          )}
          <Button size="icon" variant="ghost" onClick={handleCopy} data-testid="button-copy-code">
            <Copy className="w-4 h-4" />
          </Button>
          <Button size="icon" variant="ghost" onClick={handleDownload} data-testid="button-download-code">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto">
        <textarea
          ref={textareaRef}
          value={currentCode}
          onChange={(e) => setCurrentCode(e.target.value)}
          readOnly={readOnly}
          className="w-full h-full p-4 bg-transparent font-mono text-sm text-foreground resize-none focus:outline-none"
          placeholder="// Your automation code will appear here..."
          spellCheck={false}
          data-testid="textarea-code-editor"
        />
      </div>
    </div>
  );
}
