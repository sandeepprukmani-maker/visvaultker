import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { useAuth } from "./use-auth";
import { useToast } from "@/hooks/use-toast";

export function useScenarios() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: [api.scenarios.list.path],
    queryFn: async () => {
      const token = getToken();
      // If no token, we can't fetch, return empty or handle gracefully
      if (!token) return [];

      const res = await fetch(api.scenarios.list.path, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      if (!res.ok) {
        if (res.status === 401) return []; // Handle unauthorized by returning empty
        throw new Error("Failed to fetch scenarios");
      }
      
      return api.scenarios.list.responses[200].parse(await res.json());
    },
    enabled: !!getToken(), // Only run if we have a token
  });
}

export function useScenario(id: number) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: [api.scenarios.get.path, id],
    queryFn: async () => {
      const token = getToken();
      if (!token) throw new Error("Not authenticated");

      const url = buildUrl(api.scenarios.get.path, { id });
      const res = await fetch(url, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch scenario details");
      
      return api.scenarios.get.responses[200].parse(await res.json());
    },
    enabled: !!id && !!getToken(),
  });
}

export function useDeleteScenario() {
  const queryClient = useQueryClient();
  const { getToken } = useAuth();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken();
      if (!token) throw new Error("Not authenticated");

      const url = buildUrl(api.scenarios.delete.path, { id });
      const res = await fetch(url, {
        method: api.scenarios.delete.method,
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error("Failed to delete scenario");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.scenarios.list.path] });
      toast({
        title: "Scenario Deleted",
        description: "The scenario has been removed from your history.",
      });
    },
  });
}
