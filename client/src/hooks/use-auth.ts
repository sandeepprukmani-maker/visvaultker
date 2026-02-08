import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TokenRequest } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

// Simple local storage management for demo auth
const TOKEN_KEY = "uwm_auth_token";

export function useAuth() {
  const { toast } = useToast();

  const loginMutation = useMutation({
    mutationFn: async (credentials: Partial<TokenRequest>) => {
      // Defaulting to client_credentials flow or similar as per schema, 
      // but in this demo we'll use the provided endpoint structure.
      // Since it's a mock, we construct a valid request payload.
      const payload: TokenRequest = {
        grant_type: "password", // or client_credentials
        client_id: "demo-client",
        client_secret: "demo-secret",
        username: credentials.username || "demo",
        password: credentials.password || "demo",
        ...credentials
      };

      const res = await fetch(api.auth.token.path, {
        method: api.auth.token.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Failed to authenticate");
      }

      return api.auth.token.responses[200].parse(await res.json());
    },
    onSuccess: (data) => {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      toast({
        title: "Authenticated",
        description: "Successfully connected to pricing engine.",
      });
    },
    onError: () => {
      toast({
        title: "Authentication Failed",
        description: "Could not verify credentials.",
        variant: "destructive",
      });
    },
  });

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    window.location.reload();
  };

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const isAuthenticated = !!getToken();

  return {
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    logout,
    getToken,
    isAuthenticated,
  };
}
