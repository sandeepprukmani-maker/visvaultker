import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type GeneratePosterRequest } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

export function useLatestPost() {
  return useQuery({
    queryKey: [api.posts.latest.path],
    queryFn: async () => {
      const res = await fetch(api.posts.latest.path);
      if (!res.ok) throw new Error("Failed to fetch latest news");
      return api.posts.latest.responses[200].parse(await res.json());
    },
  });
}

export function usePosters() {
  return useQuery({
    queryKey: [api.posters.list.path],
    queryFn: async () => {
      const res = await fetch(api.posters.list.path);
      if (!res.ok) throw new Error("Failed to fetch posters");
      return api.posters.list.responses[200].parse(await res.json());
    },
  });
}

export function useGeneratePoster() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: GeneratePosterRequest) => {
      const res = await fetch(api.posters.create.path, {
        method: api.posters.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.message || "Failed to generate poster");
      }

      return api.posters.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.posters.list.path] });
      toast({
        title: "Poster Generated!",
        description: "Your social media asset has been created successfully.",
        variant: "default",
      });
    },
    onError: (error) => {
      toast({
        title: "Generation Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });
}
