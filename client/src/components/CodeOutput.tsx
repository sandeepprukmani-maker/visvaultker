import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Download, Check } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface CodeOutputProps {
  typescriptCode?: string;
  cachedCode?: string;
  agentCode?: string;
}

export default function CodeOutput({ typescriptCode, cachedCode, agentCode }: CodeOutputProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({
      title: "Copied to clipboard",
      description: "Code has been copied to your clipboard",
    });
  };

  const handleDownload = (code: string, filename: string) => {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    toast({
      title: "Downloaded",
      description: `${filename} has been downloaded`,
    });
  };

  const hasCode = typescriptCode || cachedCode || agentCode;

  return (
    <Card className="flex h-full flex-col overflow-hidden border">
      <div className="flex h-10 items-center justify-between border-b px-4">
        <h3 className="text-sm font-medium">Generated Code</h3>
        {hasCode && (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopy(typescriptCode || cachedCode || agentCode || "")}
              data-testid="button-copy-code"
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDownload(typescriptCode || "", "automation.ts")}
              data-testid="button-download-code"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-hidden">
        {!hasCode ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Generated code will appear here
            </p>
          </div>
        ) : (
          <Tabs defaultValue="typescript" className="flex h-full flex-col">
            <TabsList className="mx-4 mt-2 w-auto">
              {typescriptCode && <TabsTrigger value="typescript" data-testid="tab-typescript">TypeScript</TabsTrigger>}
              {cachedCode && <TabsTrigger value="cached" data-testid="tab-cached">Cached</TabsTrigger>}
              {agentCode && <TabsTrigger value="agent" data-testid="tab-agent">Agent</TabsTrigger>}
            </TabsList>
            <div className="flex-1 overflow-auto">
              {typescriptCode && (
                <TabsContent value="typescript" className="m-0 h-full">
                  <pre className="h-full overflow-auto bg-neutral-900 p-4 font-mono text-sm text-neutral-100">
                    <code>{typescriptCode}</code>
                  </pre>
                </TabsContent>
              )}
              {cachedCode && (
                <TabsContent value="cached" className="m-0 h-full">
                  <pre className="h-full overflow-auto bg-neutral-900 p-4 font-mono text-sm text-neutral-100">
                    <code>{cachedCode}</code>
                  </pre>
                </TabsContent>
              )}
              {agentCode && (
                <TabsContent value="agent" className="m-0 h-full">
                  <pre className="h-full overflow-auto bg-neutral-900 p-4 font-mono text-sm text-neutral-100">
                    <code>{agentCode}</code>
                  </pre>
                </TabsContent>
              )}
            </div>
          </Tabs>
        )}
      </div>
    </Card>
  );
}
