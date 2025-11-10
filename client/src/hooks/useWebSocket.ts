import { useEffect, useRef, useState, useCallback } from "react";
import type { WSMessage, LogEntry, AutomationResponse } from "@shared/schema";

interface UseWebSocketOptions {
  onLog?: (log: LogEntry) => void;
  onComplete?: (response: AutomationResponse) => void;
  onError?: (error: string) => void;
}

export function useWebSocket({ onLog, onComplete, onError }: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const currentSessionIdRef = useRef<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Use refs for callbacks to avoid dependency issues
  const onLogRef = useRef(onLog);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onLogRef.current = onLog;
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onLog, onComplete, onError]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      
      // Resubscribe to session if we have an active one (after reconnect)
      if (currentSessionIdRef.current) {
        console.log(`Resubscribing to session: ${currentSessionIdRef.current}`);
        socket.send(JSON.stringify({ type: "subscribe", sessionId: currentSessionIdRef.current }));
      }
    };

    socket.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case "log":
            onLogRef.current?.(message.log);
            break;
          case "complete":
            onCompleteRef.current?.(message.response);
            break;
          case "error":
            onErrorRef.current?.(message.error);
            break;
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
      // Attempt reconnection after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.current = socket;
  }, []);

  const subscribe = useCallback((sessionId: string) => {
    currentSessionIdRef.current = sessionId;
    
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log(`Subscribing to session: ${sessionId}`);
      ws.current.send(JSON.stringify({ type: "subscribe", sessionId }));
    } else {
      // Queue subscription for when socket opens
      console.log(`Socket not ready, subscription will occur on connect`);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    subscribe,
    currentSessionId: currentSessionIdRef.current,
  };
}
