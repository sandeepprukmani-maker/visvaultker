import { useState, useRef, useEffect } from "react";
import { type Message, type AutomationTask, type ConnectionStatus } from "@shared/schema";
import { ChatMessage } from "@/components/chat-message";
import { PromptInput } from "@/components/prompt-input";
import { EmptyState } from "@/components/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface HomeProps {
  onNewTask: (task: AutomationTask) => void;
  onTaskUpdate: (task: AutomationTask) => void;
  activeTask?: AutomationTask | null;
  connectionStatus: ConnectionStatus;
}

export default function Home({ 
  onNewTask, 
  onTaskUpdate, 
  activeTask,
  connectionStatus 
}: HomeProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (activeTask) {
      const taskMessages: Message[] = [
        {
          id: `user-${activeTask.id}`,
          role: "user",
          content: activeTask.prompt,
          timestamp: activeTask.createdAt,
          taskId: activeTask.id,
        },
      ];

      if (activeTask.status === "running") {
        taskMessages.push({
          id: `running-${activeTask.id}`,
          role: "assistant",
          content: "Executing browser automation...",
          timestamp: Date.now(),
          taskId: activeTask.id,
          actions: activeTask.actions,
        });
      } else if (activeTask.status === "success") {
        taskMessages.push({
          id: `result-${activeTask.id}`,
          role: "assistant",
          content: activeTask.result || "Automation completed successfully!",
          timestamp: activeTask.completedAt || Date.now(),
          taskId: activeTask.id,
          actions: activeTask.actions,
        });
      } else if (activeTask.status === "error") {
        taskMessages.push({
          id: `error-${activeTask.id}`,
          role: "assistant",
          content: activeTask.error || "An error occurred during automation.",
          timestamp: activeTask.completedAt || Date.now(),
          taskId: activeTask.id,
          actions: activeTask.actions,
        });
      }

      setMessages(taskMessages);
    }
  }, [activeTask]);

  const executeMutation = useMutation({
    mutationFn: async (prompt: string) => {
      const response = await apiRequest("POST", "/api/execute", { prompt });
      return response as AutomationTask;
    },
    onMutate: (prompt) => {
      const tempId = `temp-${Date.now()}`;
      const userMessage: Message = {
        id: `user-${tempId}`,
        role: "user",
        content: prompt,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);
    },
    onSuccess: (task) => {
      onNewTask(task);
      queryClient.invalidateQueries({ queryKey: ["/api/tasks"] });
    },
    onError: (error: Error) => {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: error.message || "Failed to execute automation. Please try again.",
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast({
        variant: "destructive",
        title: "Execution Failed",
        description: error.message,
      });
    },
  });

  const handleSubmit = (prompt: string) => {
    if (connectionStatus === "disconnected") {
      toast({
        variant: "destructive",
        title: "Not Connected",
        description: "Please wait for the browser to connect.",
      });
      return;
    }
    executeMutation.mutate(prompt);
  };

  const handleExampleClick = (prompt: string) => {
    handleSubmit(prompt);
  };

  return (
    <div className="flex flex-col h-full">
      {messages.length === 0 ? (
        <EmptyState onExampleClick={handleExampleClick} />
      ) : (
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="flex flex-col gap-4 p-6 max-w-4xl mx-auto">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </div>
        </ScrollArea>
      )}
      
      <PromptInput
        onSubmit={handleSubmit}
        isLoading={executeMutation.isPending}
        disabled={connectionStatus === "disconnected"}
      />
    </div>
  );
}
