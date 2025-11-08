import { Video, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Todo: remove mock data
const mockRecordings = [
  {
    id: "1",
    name: "Login Flow Recording",
    duration: "2m 34s",
    date: "2 hours ago",
    actions: 12,
  },
  {
    id: "2",
    name: "Checkout Process",
    duration: "4m 12s",
    date: "1 day ago",
    actions: 24,
  },
  {
    id: "3",
    name: "Search and Filter",
    duration: "1m 45s",
    date: "2 days ago",
    actions: 8,
  },
];

export default function Recordings() {
  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recordings</h2>
          <Button variant="default" data-testid="button-start-recording">
            <Video className="w-4 h-4 mr-2" />
            Start Recording
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockRecordings.map((recording) => (
            <Card key={recording.id} className="hover-elevate" data-testid={`card-recording-${recording.id}`}>
              <CardHeader>
                <div className="flex items-start gap-2">
                  <div className="w-10 h-10 rounded bg-primary/10 flex items-center justify-center">
                    <Video className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-medium">{recording.name}</h4>
                    <p className="text-xs text-muted-foreground">{recording.date}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{recording.duration}</span>
                  <span>•</span>
                  <span>{recording.actions} actions</span>
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button size="sm" variant="default" className="flex-1" data-testid={`button-replay-${recording.id}`}>
                  <Play className="w-3 h-3 mr-1" />
                  Replay
                </Button>
                <Button size="sm" variant="secondary" className="flex-1" data-testid={`button-convert-${recording.id}`}>
                  Convert to Code
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {mockRecordings.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-2">
              <Video className="w-12 h-12 text-muted-foreground mx-auto" />
              <p className="text-sm text-muted-foreground">No recordings yet</p>
              <Button size="sm" data-testid="button-create-first-recording">
                <Video className="w-4 h-4 mr-2" />
                Create Your First Recording
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
