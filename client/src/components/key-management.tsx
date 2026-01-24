import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { Trash2, Key, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function KeyManagement() {
  const [newKey, setNewKey] = useState("");
  const { toast } = useToast();

  const { data: keys, isLoading } = useQuery<any[]>({
    queryKey: ["/api/keys"],
  });

  const addMutation = useMutation({
    mutationFn: async (key: string) => {
      const res = await apiRequest("POST", "/api/keys", { key });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/keys"] });
      setNewKey("");
      toast({ title: "API Key added successfully" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiRequest("DELETE", `/api/keys/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/keys"] });
      toast({ title: "API Key deleted" });
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Key className="w-5 h-5" />
          HeyGen API Keys
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="Enter HeyGen API Key"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            type="password"
            data-testid="input-api-key"
          />
          <Button
            onClick={() => newKey && addMutation.mutate(newKey)}
            disabled={addMutation.isPending || !newKey}
            data-testid="button-add-key"
          >
            Add Key
          </Button>
        </div>

        <div className="space-y-2">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Loading keys...</div>
          ) : keys?.length === 0 ? (
            <div className="text-sm text-muted-foreground italic">No extra keys added yet. System will use environment default.</div>
          ) : (
            keys?.map((k) => (
              <div
                key={k.id}
                className="flex items-center justify-between p-2 rounded-md border bg-muted/30"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  {k.isActive === "true" ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-destructive shrink-0" />
                  )}
                  <code className="text-xs truncate">{k.key}</code>
                  {k.lastUsedAt && (
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                      Used: {new Date(k.lastUsedAt).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => deleteMutation.mutate(k.id)}
                  disabled={deleteMutation.isPending}
                  data-testid={`button-delete-key-${k.id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
