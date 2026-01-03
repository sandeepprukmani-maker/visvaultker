import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type QuoteInput } from "@shared/routes";

// GET /api/quotes
export function useQuotes() {
  return useQuery({
    queryKey: [api.quotes.list.path],
    queryFn: async () => {
      const res = await fetch(api.quotes.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch quotes");
      return api.quotes.list.responses[200].parse(await res.json());
    },
  });
}

// POST /api/quotes/generate
export function useGenerateQuote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: QuoteInput) => {
      const res = await fetch(api.quotes.generate.path, {
        method: api.quotes.generate.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 500) {
          const error = api.quotes.generate.responses[500].parse(await res.json());
          throw new Error(error.message);
        }
        throw new Error("Failed to generate quote");
      }
      return api.quotes.generate.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.quotes.list.path] });
    },
  });
}
