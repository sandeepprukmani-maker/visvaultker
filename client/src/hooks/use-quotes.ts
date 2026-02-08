import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type MortgageQuoteRequest, type HelocQuoteRequest } from "@shared/routes";
import { useAuth } from "./use-auth";
import { useToast } from "@/hooks/use-toast";

export function useMortgageQuote() {
  const { getToken } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MortgageQuoteRequest) => {
      const token = getToken();
      if (!token) throw new Error("Not authenticated");

      const res = await fetch(api.quotes.mortgage.path, {
        method: api.quotes.mortgage.method,
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}` 
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        if (res.status === 401) throw new Error("Unauthorized");
        const error = await res.json();
        throw new Error(error.message || "Failed to get quote");
      }

      return api.quotes.mortgage.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.scenarios.list.path] });
      toast({
        title: "Quote Generated",
        description: "Successfully retrieved pricing options.",
      });
    },
    onError: (error) => {
      toast({
        title: "Quote Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });
}

export function useHelocQuote() {
  const { getToken } = useAuth();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: HelocQuoteRequest) => {
      const token = getToken();
      if (!token) throw new Error("Not authenticated");

      const res = await fetch(api.quotes.heloc.path, {
        method: api.quotes.heloc.method,
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) throw new Error("Failed to get HELOC quote");

      return api.quotes.heloc.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      toast({
        title: "HELOC Quote Generated",
        description: "Successfully retrieved pricing options.",
      });
    },
  });
}
