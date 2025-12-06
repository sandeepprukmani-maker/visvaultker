import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

let client: Client | null = null;
let transport: StdioClientTransport | null = null;
let isConnected = false;

export async function initMcpClient(): Promise<Client> {
  if (client && isConnected) {
    return client;
  }

  try {
    console.log("Starting Playwright MCP server...");

    transport = new StdioClientTransport({
      command: "npx",
      args: ["@playwright/mcp@latest", "--headless"],
      env: {
        ...process.env,
        XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME || "/tmp/.config",
      },
    });

    client = new Client({
      name: "browser-pilot",
      version: "1.0.0",
    });

    transport.onerror = (error) => {
      console.error("MCP transport error:", error);
      isConnected = false;
    };

    transport.onclose = () => {
      console.log("MCP transport closed");
      isConnected = false;
      client = null;
    };

    await client.connect(transport);
    isConnected = true;
    console.log("Connected to Playwright MCP server");

    const tools = await client.listTools();
    console.log("Available MCP tools:", tools.tools.map((t) => t.name));

    return client;
  } catch (error) {
    console.error("Failed to connect to MCP server:", error);
    throw error;
  }
}

export async function getMcpClient(): Promise<Client | null> {
  if (!client || !isConnected) {
    try {
      return await initMcpClient();
    } catch {
      return null;
    }
  }
  return client;
}

export function getConnectionStatus(): "connected" | "disconnected" | "connecting" {
  if (isConnected && client) return "connected";
  if (!client) return "disconnected";
  return "connecting";
}

export async function callMcpTool(
  toolName: string,
  args: Record<string, unknown>
): Promise<unknown> {
  const mcpClient = await getMcpClient();
  if (!mcpClient) {
    throw new Error("MCP client not connected");
  }

  try {
    const result = await mcpClient.callTool({
      name: toolName,
      arguments: args,
    });
    return result;
  } catch (error) {
    console.error(`Error calling MCP tool ${toolName}:`, error);
    throw error;
  }
}

export async function listMcpTools(): Promise<string[]> {
  const mcpClient = await getMcpClient();
  if (!mcpClient) {
    return [];
  }

  try {
    const tools = await mcpClient.listTools();
    return tools.tools.map((t) => t.name);
  } catch {
    return [];
  }
}

export async function closeMcpClient(): Promise<void> {
  if (client) {
    try {
      await client.close();
    } catch (error) {
      console.error("Error closing MCP client:", error);
    }
    client = null;
    isConnected = false;
  }

  if (transport) {
    try {
      await transport.close();
    } catch (error) {
      console.error("Error closing transport:", error);
    }
    transport = null;
  }
}
