import { useEffect, useRef, useState } from "react";
import type { WebSocketMessage } from "@shared/schema";

export function useWebSocket(onMessage?: (message: WebSocketMessage) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket server on the backend port
    // In development, Vite runs on :5173 but backend is on :5000
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const backendHost = import.meta.env.DEV 
      ? `${window.location.hostname}:5000` 
      : window.location.host;
    const wsUrl = `${protocol}//${backendHost}/ws`;

    console.log('Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        onMessage?.(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [onMessage]);

  return { isConnected, ws: wsRef.current };
}
