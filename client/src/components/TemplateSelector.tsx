import { useState } from "react";
import { Globe, FileText, Database, TestTube2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useQuery } from "@tanstack/react-query";
import type { AutomationTemplate } from "@shared/schema";

interface TemplateSelectorProps {
  onSelectTemplate: (prompt: string) => void;
}

const iconMap: Record<string, any> = {
  Globe,
  FileText,
  Database,
  TestTube2,
};

export function TemplateSelector({ onSelectTemplate }: TemplateSelectorProps) {
  const [open, setOpen] = useState(false);

  const { data: templates = [] } = useQuery<AutomationTemplate[]>({
    queryKey: ["/api/templates"],
  });

  const handleSelect = (prompt: string) => {
    setOpen(false);
    onSelectTemplate(prompt);
  };

  return (
    <div className="mb-6">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground hover:text-foreground"
            data-testid="button-show-templates"
          >
            <FileText className="w-4 h-4 mr-2" />
            Choose from templates
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-96 p-0" align="start">
          <div className="p-4 border-b">
            <h3 className="font-medium text-sm">Quick Templates</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Start with a pre-built automation
            </p>
          </div>
          <div className="p-2 max-h-96 overflow-y-auto">
            {templates.map((template) => {
              const Icon = iconMap[template.icon] || FileText;
              return (
                <button
                  key={template.id}
                  onClick={() => handleSelect(template.prompt)}
                  className="w-full p-3 rounded-lg hover-elevate text-left"
                  data-testid={`template-${template.id}`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 flex-shrink-0 mt-0.5">
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium" data-testid={`template-name-${template.id}`}>
                        {template.name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {template.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
