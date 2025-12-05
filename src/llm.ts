import OpenAI from 'openai';
import type { MCPTool } from './mcp-client.js';

// Using gpt-4o-mini as requested by user
const MODEL = 'gpt-4o-mini';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface LLMResponse {
  thinking: string;
  toolCalls: ToolCall[];
  done: boolean;
  summary?: string;
}

export async function interpretPrompt(
  userPrompt: string,
  availableTools: MCPTool[],
  previousActions: string[] = [],
  lastToolResult?: string
): Promise<LLMResponse> {
  const toolsDescription = availableTools.map(tool => {
    const params = tool.inputSchema?.properties 
      ? JSON.stringify(tool.inputSchema.properties)
      : '{}';
    const required = tool.inputSchema?.required || [];
    return `- ${tool.name}: ${tool.description || 'No description'}
    Parameters: ${params}
    Required: ${required.join(', ') || 'none'}`;
  }).join('\n\n');

  const systemPrompt = `You are a browser automation assistant that uses Playwright MCP tools to automate web browsers.

Available tools:
${toolsDescription}

Important guidelines:
1. Break down the user's request into individual tool calls
2. Execute one tool at a time to ensure proper sequencing
3. Always start by navigating to a URL if the user mentions a website
4. Use browser_snapshot to see the current page state when needed
5. Use browser_click to click on elements
6. Use browser_type to enter text into input fields
7. Use browser_press_key to press keys like Enter, Tab, etc.
8. Set done=true when the task is complete or you've achieved the user's goal

Respond with JSON in this exact format:
{
  "thinking": "Your reasoning about what to do next",
  "toolCalls": [{"name": "tool_name", "arguments": {...}}],
  "done": false,
  "summary": "Summary when done (only when done=true)"
}

Only include ONE tool call at a time to ensure proper sequencing.`;

  const userMessage = previousActions.length > 0
    ? `Original request: "${userPrompt}"

Previous actions taken:
${previousActions.map((a, i) => `${i + 1}. ${a}`).join('\n')}

${lastToolResult ? `Last tool result: ${lastToolResult}` : ''}

What should be the next step?`
    : `User request: "${userPrompt}"

What tool calls are needed to accomplish this task?`;

  try {
    const response = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ],
      response_format: { type: 'json_object' },
    });

    const content = response.choices[0].message.content;
    if (!content) {
      throw new Error('Empty response from LLM');
    }

    const parsed = JSON.parse(content) as LLMResponse;
    return parsed;
  } catch (error) {
    if (error instanceof Error) {
      if (error.message.includes('429') || error.message.includes('quota')) {
        throw new Error('OpenAI API rate limit or quota exceeded. Please check your API key billing status.');
      }
      if (error.message.includes('401') || error.message.includes('invalid_api_key')) {
        throw new Error('Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable.');
      }
    }
    throw error;
  }
}

export async function summarizeResults(
  originalPrompt: string,
  actions: string[],
  results: string[]
): Promise<string> {
  const response = await openai.chat.completions.create({
    model: MODEL,
    messages: [
      {
        role: 'system',
        content: 'You are a helpful assistant that summarizes browser automation results concisely.',
      },
      {
        role: 'user',
        content: `Original request: "${originalPrompt}"

Actions performed:
${actions.map((a, i) => `${i + 1}. ${a}`).join('\n')}

Results:
${results.join('\n')}

Provide a brief summary of what was accomplished.`,
      },
    ],
  });

  return response.choices[0].message.content || 'Task completed.';
}
