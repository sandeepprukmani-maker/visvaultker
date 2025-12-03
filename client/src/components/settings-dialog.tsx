import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Settings, Cpu, Zap } from "lucide-react";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid="dialog-settings">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Settings
          </DialogTitle>
          <DialogDescription>
            Configure your Eko automation preferences
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              <h3 className="font-medium">AI Model</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="model-select" className="text-sm">
                  Default Model
                </Label>
                <Select defaultValue="claude-sonnet">
                  <SelectTrigger className="w-48" id="model-select" data-testid="select-model">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="claude-sonnet">
                      <div className="flex items-center gap-2">
                        Claude Sonnet 4
                        <Badge variant="secondary" className="text-xs">Recommended</Badge>
                      </div>
                    </SelectItem>
                    <SelectItem value="claude-haiku">Claude Haiku</SelectItem>
                    <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <h3 className="font-medium">Execution</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="auto-execute" className="text-sm">
                    Auto-execute workflows
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Start execution immediately after planning
                  </p>
                </div>
                <Switch id="auto-execute" defaultChecked data-testid="switch-auto-execute" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="parallel-exec" className="text-sm">
                    Parallel execution
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Run independent steps in parallel
                  </p>
                </div>
                <Switch id="parallel-exec" defaultChecked data-testid="switch-parallel-exec" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="verbose-logs" className="text-sm">
                    Verbose logging
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Show detailed execution logs
                  </p>
                </div>
                <Switch id="verbose-logs" data-testid="switch-verbose-logs" />
              </div>
            </div>
          </div>

          <Separator />

          <div className="rounded-lg bg-muted/50 p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Eko Framework</p>
                <p className="text-xs text-muted-foreground">Version 3.0</p>
              </div>
              <Badge variant="outline" className="text-xs">
                Production Ready
              </Badge>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
