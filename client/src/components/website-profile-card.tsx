import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Globe, Eye, RefreshCw, Calendar } from "lucide-react";

interface WebsiteProfileCardProps {
  id: string;
  url: string;
  elementCount: number;
  lastLearned: string;
  version: number;
  status: "learned" | "learning" | "outdated";
  onView?: () => void;
  onRelearn?: () => void;
}

export function WebsiteProfileCard({
  id,
  url,
  elementCount,
  lastLearned,
  version,
  status,
  onView,
  onRelearn,
}: WebsiteProfileCardProps) {
  const statusColors = {
    learned: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
    learning: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
    outdated: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20",
  };

  return (
    <Card className="hover-elevate" data-testid={`website-profile-${id}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="h-4 w-4 text-primary" />
              <CardTitle className="text-lg break-all">{url}</CardTitle>
            </div>
            <CardDescription>{elementCount} elements mapped</CardDescription>
          </div>
          <Badge className={statusColors[status]} variant="outline">
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>Last learned: {lastLearned}</span>
          </div>
          <div className="text-sm text-muted-foreground">
            Version: {version}
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button size="sm" variant="outline" onClick={onView} data-testid={`button-view-${id}`}>
          <Eye className="h-3 w-3 mr-1" />
          View Map
        </Button>
        <Button size="sm" variant="outline" onClick={onRelearn} data-testid={`button-relearn-${id}`}>
          <RefreshCw className="h-3 w-3 mr-1" />
          Re-learn
        </Button>
      </CardFooter>
    </Card>
  );
}
