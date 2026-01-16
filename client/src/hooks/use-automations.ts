import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl, type InsertAutomation } from "@shared/routes";

// GET /api/automations
export function useAutomations() {
  return useQuery({
    queryKey: [api.automations.list.path],
    queryFn: async () => {
      const res = await fetch(api.automations.list.path);
      if (!res.ok) throw new Error("Failed to fetch automations");
      return api.automations.list.responses[200].parse(await res.json());
    },
  });
}

// GET /api/automations/:id
export function useAutomation(id: number) {
  return useQuery({
    queryKey: [api.automations.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.automations.get.path, { id });
      const res = await fetch(url);
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch automation");
      return api.automations.get.responses[200].parse(await res.json());
    },
    // Poll every 1 second if status is running or pending
    refetchInterval: (data) => 
      (data?.status === 'running' || data?.status === 'pending') ? 1000 : false,
  });
}

// POST /api/automations
export function useCreateAutomation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: InsertAutomation) => {
      const validated = api.automations.create.input.parse(data);
      const res = await fetch(api.automations.create.path, {
        method: api.automations.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(validated),
      });
      
      if (!res.ok) {
        if (res.status === 400) {
          const error = api.automations.create.responses[400].parse(await res.json());
          throw new Error(error.message);
        }
        throw new Error("Failed to create automation");
      }
      return api.automations.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.automations.list.path] });
    },
  });
}
