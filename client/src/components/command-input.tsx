import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { Send, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { apiRequest, queryClient } from "@/lib/queryClient"

const suggestions = [
  "Login as admin",
  "Add a new user",
  "Search for John Doe",
  "Delete the first item",
]

interface CommandInputProps {
  onExecute?: (command: string) => void
  isExecuting?: boolean
}

export function CommandInput({ onExecute, isExecuting: externalIsExecuting = false }: CommandInputProps) {
  const [command, setCommand] = useState("")
  const { toast } = useToast()

  const executeMutation = useMutation({
    mutationFn: async (command: string) => {
      const response = await apiRequest("POST", "/api/automations", { command })
      return await response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/automations"] })
      queryClient.invalidateQueries({ queryKey: ["/api/stats"] })
      toast({
        title: "Automation Started",
        description: "Your command is being executed",
      })
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to execute command",
        variant: "destructive",
      })
    },
  })

  const isExecuting = externalIsExecuting || executeMutation.isPending

  const handleExecute = () => {
    if (command.trim()) {
      executeMutation.mutate(command)
      onExecute?.(command)
      setCommand("")
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setCommand(suggestion)
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Textarea
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Enter command: 'Login as admin' or 'Add a new user'..."
          className="min-h-[100px] resize-none pr-12 text-base"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault()
              handleExecute()
            }
          }}
          data-testid="input-command"
        />
        <Button
          size="icon"
          onClick={handleExecute}
          disabled={!command.trim() || isExecuting}
          className="absolute bottom-3 right-3"
          data-testid="button-execute"
        >
          {isExecuting ? (
            <Sparkles className="h-4 w-4 animate-pulse" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
      
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Quick actions:</span>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <Badge
              key={suggestion}
              variant="secondary"
              className="cursor-pointer hover-elevate active-elevate-2"
              onClick={() => handleSuggestionClick(suggestion)}
              data-testid={`suggestion-${suggestion.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {suggestion}
            </Badge>
          ))}
        </div>
      </div>
      
      <p className="text-xs text-muted-foreground">
        Press <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">⌘+Enter</kbd> to execute
      </p>
    </div>
  )
}
