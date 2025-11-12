import { WebSocketServer, WebSocket } from "ws";
import type { Server } from "http";
import type { WSMessage } from "@shared/schema";

const sessions = new Map<string, Set<WebSocket>>();

export function setupWebSocket(server: Server): WebSocketServer {
  const wss = new WebSocketServer({ server, path: "/ws" });

  wss.on("connection", (ws: WebSocket) => {
    console.log("WebSocket client connected");

    ws.on("message", (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());
        
        // Client subscribing to a session
        if (message.type === "subscribe" && message.sessionId) {
          if (!sessions.has(message.sessionId)) {
            sessions.set(message.sessionId, new Set());
          }
          sessions.get(message.sessionId)!.add(ws);
          console.log(`Client subscribed to session: ${message.sessionId}`);
        }
      } catch (error) {
        console.error("WebSocket message error:", error);
      }
    });

    ws.on("close", () => {
      // Remove this socket from all sessions
      sessions.forEach((clients, sessionId) => {
        clients.delete(ws);
        if (clients.size === 0) {
          sessions.delete(sessionId);
        }
      });
      console.log("WebSocket client disconnected");
    });

    ws.on("error", (error) => {
      console.error("WebSocket error:", error);
    });
  });

  return wss;
}

export function broadcastToSession(sessionId: string, message: WSMessage): void {
  const clients = sessions.get(sessionId);
  if (!clients) return;

  const data = JSON.stringify(message);
  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
}
