import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Globe, FileText, Database, Search, Code, Bot } from "lucide-react";
import type { Template } from "@shared/schema";

const TEMPLATES: Template[] = [
  {
    id: "web-scraping",
    title: "Web Scraping",
    description: "Extract data from any website including prices, text, images, and more",
    prompt: "Scrape all product names and prices from the website at [URL]",
    icon: "globe",
    category: "scraping",
  },
  {
    id: "form-automation",
    title: "Form Automation",
    description: "Automatically fill out web forms with specified data",
    prompt: "Fill out the contact form at [URL] with the following information: [DATA]",
    icon: "file-text",
    category: "forms",
  },
  {
    id: "data-extraction",
    title: "Data Extraction",
    description: "Extract structured data like emails, phone numbers, or links",
    prompt: "Extract all email addresses and phone numbers from [URL]",
    icon: "database",
    category: "extraction",
  },
  {
    id: "multi-step-research",
    title: "Multi-step Research",
    description: "Research a topic across multiple sources and compile findings",
    prompt: "Research [TOPIC] across multiple sources and create a summary report",
    icon: "search",
    category: "research",
  },
  {
    id: "api-interaction",
    title: "API Interaction",
    description: "Interact with web APIs to fetch or submit data",
    prompt: "Fetch data from [API_URL] and process the response",
    icon: "code",
    category: "custom",
  },
  {
    id: "custom-workflow",
    title: "Custom Workflow",
    description: "Create a custom multi-step automation workflow",
    prompt: "Create a workflow that [DESCRIBE YOUR TASK]",
    icon: "bot",
    category: "custom",
  },
];

const iconMap: Record<string, React.ReactNode> = {
  globe: <Globe className="h-8 w-8" />,
  "file-text": <FileText className="h-8 w-8" />,
  database: <Database className="h-8 w-8" />,
  search: <Search className="h-8 w-8" />,
  code: <Code className="h-8 w-8" />,
  bot: <Bot className="h-8 w-8" />,
};

const categoryColors: Record<string, string> = {
  scraping: "from-purple-500/10 to-purple-600/10 text-purple-600 dark:text-purple-400",
  forms: "from-blue-500/10 to-blue-600/10 text-blue-600 dark:text-blue-400",
  extraction: "from-green-500/10 to-green-600/10 text-green-600 dark:text-green-400",
  research: "from-orange-500/10 to-orange-600/10 text-orange-600 dark:text-orange-400",
  custom: "from-pink-500/10 to-pink-600/10 text-pink-600 dark:text-pink-400",
};

interface TemplateCardsProps {
  onSelectTemplate: (prompt: string) => void;
}

export function TemplateCards({ onSelectTemplate }: TemplateCardsProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Quick Templates</h2>
        <p className="text-sm text-muted-foreground">
          Start with a pre-built automation template
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {TEMPLATES.map((template) => (
          <Card
            key={template.id}
            className="group cursor-pointer transition-all duration-200 hover-elevate"
            onClick={() => onSelectTemplate(template.prompt)}
            data-testid={`card-template-${template.id}`}
          >
            <CardHeader className="pb-3">
              <div
                className={`mb-3 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${
                  categoryColors[template.category]
                }`}
              >
                {iconMap[template.icon]}
              </div>
              <CardTitle className="text-lg">{template.title}</CardTitle>
              <CardDescription className="text-sm">
                {template.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="secondary"
                size="sm"
                className="w-full"
                data-testid={`button-use-template-${template.id}`}
              >
                Use Template
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
