import { useState, useEffect, useRef } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Mic, MicOff } from "lucide-react";
import { useSettings } from "@/contexts/SettingsContext";
import { useToast } from "@/hooks/use-toast";

interface UnifiedAutomationInputProps {
  onExecute: (data: { prompt: string; model: string }) => void;
  isExecuting: boolean;
}

export default function UnifiedAutomationInput({
  onExecute,
  isExecuting,
}: UnifiedAutomationInputProps) {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { model } = useSettings();
  const { toast } = useToast();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = false;
        recognitionInstance.lang = 'en-US';

        recognitionInstance.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setPrompt(transcript);
          setIsListening(false);
        };

        recognitionInstance.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          setIsListening(false);
          toast({
            title: "Voice input error",
            description: "Could not recognize speech. Please try again.",
            variant: "destructive",
          });
        };

        recognitionInstance.onend = () => {
          setIsListening(false);
        };

        setRecognition(recognitionInstance);
      }
    }
  }, [toast]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onExecute({ prompt, model });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (prompt.trim()) {
        onExecute({ prompt, model });
        setPrompt("");
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    autoResize();
  };

  const autoResize = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  useEffect(() => {
    autoResize();
  }, [prompt]);

  const toggleVoiceInput = () => {
    if (!recognition) {
      toast({
        title: "Voice input not supported",
        description: "Your browser doesn't support voice input. Please use Chrome, Edge, or Safari.",
        variant: "destructive",
      });
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
      toast({
        title: "Listening...",
        description: "Speak now to input your automation task",
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <Textarea
        ref={textareaRef}
        data-testid="input-prompt"
        placeholder="What do you want to automate?"
        value={prompt}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={isExecuting}
        className="w-full min-h-16 max-h-96 pl-16 pr-16 py-5 text-lg rounded-3xl shadow-sm border-2 focus-visible:ring-2 text-center placeholder:text-center resize-none overflow-y-auto"
        rows={1}
      />
      <button
        type="button"
        onClick={toggleVoiceInput}
        disabled={isExecuting}
        data-testid="button-voice-input"
        className={`absolute right-5 top-5 h-8 w-8 flex items-center justify-center rounded-full hover:bg-muted/50 transition-colors ${
          isListening ? 'text-red-500 animate-pulse' : 'text-muted-foreground hover:text-foreground'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
      </button>
    </form>
  );
}
