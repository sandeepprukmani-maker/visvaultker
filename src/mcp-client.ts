import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import chalk from 'chalk';

export interface MCPTool {
  name: string;
  description?: string;
  inputSchema?: {
    type: string;
    properties?: Record<string, unknown>;
    required?: string[];
  };
}

export class PlaywrightMCPClient {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private tools: MCPTool[] = [];

  async connect(headless: boolean = false): Promise<void> {
    console.log(chalk.gray('Connecting to Playwright MCP server...'));

    // Use Playwright's bundled chromium, no external path
    const args = [
      '@playwright/mcp@latest',
      '--browser',
      'chromium'
    ];

    if (headless) {
      args.push('--headless');
    }

    this.transport = new StdioClientTransport({
      command: 'npx',
      args,
      env: {
        ...process.env,
        XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME || '/tmp/.config',
        HOME: process.env.HOME || '/tmp',

        // Allow Playwright MCP to download browsers normally
        PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD: '0',
      },
    });

    this.client = new Client(
      { name: 'playwright-mcp-cli', version: '1.0.0' },
      { capabilities: {} }
    );

    await this.client.connect(this.transport);
    console.log(chalk.green('✓ Connected to Playwright MCP server'));

    const toolsResult = await this.client.listTools();
    this.tools = toolsResult.tools as MCPTool[];
    console.log(chalk.gray(`Available tools: ${this.tools.map(t => t.name).join(', ')}`));
  }

  async disconnect(): Promise<void> {
    if (this.transport) {
      await this.transport.close();
      this.client = null;
      this.transport = null;
      console.log(chalk.gray('Disconnected from Playwright MCP server'));
    }
  }

  getTools(): MCPTool[] {
    return this.tools;
  }

  getToolsDescription(): string {
    return this.tools.map(tool => {
      const params = tool.inputSchema?.properties
        ? Object.entries(tool.inputSchema.properties)
            .map(([key, value]) => `${key}: ${(value as { type?: string }).type || 'any'}`)
            .join(', ')
        : 'no parameters';
      return `- ${tool.name}: ${tool.description || 'No description'} (${params})`;
    }).join('\n');
  }

  async callTool(name: string, args: Record<string, unknown>): Promise<unknown> {
    if (!this.client) {
      throw new Error('Not connected to MCP server');
    }

    console.log(chalk.cyan(`→ Calling tool: ${name}`));
    console.log(chalk.gray(`  Args: ${JSON.stringify(args)}`));

    try {
      const result = await this.client.callTool({ name, arguments: args });

      if (result.content && Array.isArray(result.content)) {
        for (const item of result.content) {
          if (item.type === 'text') {
            console.log(
              chalk.green(
                `  ✓ Result: ${(item as { text: string }).text.slice(0, 200)}${
                  (item as { text: string }).text.length > 200 ? '...' : ''
                }`
              )
            );
          } else if (item.type === 'image') {
            console.log(chalk.green(`  ✓ Image captured`));
          }
        }
      }

      return result;
    } catch (error) {
      console.error(
        chalk.red(
          `  ✗ Tool call failed: ${
            error instanceof Error ? error.message : error
          }`
        )
      );
      throw error;
    }
  }
}
