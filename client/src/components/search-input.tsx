import { Mic, MicOff, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useState, FormEvent, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

interface SearchInputProps {
  onSubmit: (prompt: string) => void;
  isExecuting?: boolean;
  centered?: boolean;
}

export function SearchInput({ onSubmit, isExecuting = false, centered = true }: SearchInputProps) {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const { toast } = useToast();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isExecuting) {
      onSubmit(prompt.trim());
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast({
        title: "Not Supported",
        description: "Speech recognition is not supported in your browser.",
        variant: "destructive",
      });
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setPrompt(transcript);
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      toast({
        title: "Error",
        description: "Could not capture voice input. Please try again.",
        variant: "destructive",
      });
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`w-full max-w-2xl transition-all duration-300 ${
        centered ? "mx-auto" : ""
      }`}
    >
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/20 via-primary/10 to-primary/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-300" />
        
        <div className="relative flex items-start gap-2 bg-card border border-border rounded-3xl shadow-lg hover:shadow-xl focus-within:shadow-xl transition-shadow duration-200 px-6 py-4">
          <button
            type="button"
            onClick={handleVoiceInput}
            disabled={isExecuting || isListening}
            className="mt-1 h-5 w-5 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0 disabled:opacity-50"
            data-testid="button-voice-input"
            aria-label="Voice input"
          >
            {isListening ? (
              <MicOff className="h-5 w-5 text-destructive animate-pulse" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </button>
          
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to automate..."
            className="flex-1 border-0 focus-visible:ring-0 bg-transparent text-base placeholder:text-muted-foreground resize-none min-h-[24px] max-h-32"
            disabled={isExecuting}
            data-testid="input-prompt"
            aria-label="Automation prompt"
            rows={1}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 128) + 'px';
            }}
          />
          
          <Button
            type="submit"
            size="sm"
            disabled={!prompt.trim() || isExecuting}
            className="rounded-full px-4 gap-1.5 flex-shrink-0"
            data-testid="button-execute"
          >
            <Sparkles className="h-4 w-4" />
            <span className="font-medium">Execute</span>
          </Button>
        </div>
      </div>
    </form>
  );
}
