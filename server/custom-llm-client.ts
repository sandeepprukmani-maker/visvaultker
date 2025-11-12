import { LLMClient, type LLMResponse, type AvailableModel } from "@browserbasehq/stagehand";
import https from "https";

interface ChatCompletionOptions {
  messages: Array<{
    role: string;
    content: string | any;
  }>;
  temperature?: number;
  maxTokens?: number;
  tools?: any[];
  tool_choice?: any;
}

export class CustomLLMClient extends LLMClient {
  type = "custom";
  private apiEndpoint: string;
  private apiKey: string;
  private actualModelName: string;

  constructor({
    modelName = "gpt-4o" as AvailableModel,
    apiEndpoint,
    apiKey,
    actualModelName,
  }: {
    modelName?: AvailableModel;
    apiEndpoint: string;
    apiKey: string;
    actualModelName: string;
  }) {
    super(modelName);
    this.apiEndpoint = apiEndpoint;
    this.apiKey = apiKey;
    this.actualModelName = actualModelName;
    this.hasVision = false;
  }

  async createChatCompletion<T = LLMResponse>(
    options: any,
    logger?: any,
    retries = 3
  ): Promise<T> {
    const { messages, temperature, maxTokens } = options as ChatCompletionOptions;
    try {
      const requestPayload: any = {
        model: this.actualModelName,
        messages: messages.map((msg) => ({
          role: msg.role,
          content: typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content),
        })),
        temperature,
        max_tokens: maxTokens,
      };

      if (options.tools && options.tools.length > 0) {
        requestPayload.tools = options.tools.map((tool: any) => {
          if ('function' in tool) return tool;
          return {
            type: 'type' in tool ? tool.type : "function",
            function: {
              name: tool.name,
              description: tool.description,
              parameters: tool.parameters,
            },
          };
        });
      }

      if (options.tool_choice) {
        requestPayload.tool_choice = options.tool_choice;
      }

      const requestBody = JSON.stringify(requestPayload);
      const url = new URL(this.apiEndpoint);

      const optionsHttps = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname + url.search,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.apiKey}`,
          "Content-Length": Buffer.byteLength(requestBody),
        },
        rejectUnauthorized: false,
      };

      const data = await new Promise<any>((resolve, reject) => {
        const req = https.request(optionsHttps, (res) => {
          let responseData = "";
          res.on("data", (chunk) => {
            responseData += chunk;
          });
          res.on("end", () => {
            if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
              try {
                resolve(JSON.parse(responseData));
              } catch (e) {
                reject(new Error(`Failed to parse response: ${responseData}`));
              }
            } else {
              reject(new Error(`API request failed with status ${res.statusCode}: ${responseData}`));
            }
          });
        });
        req.on("error", (error) => reject(error));
        req.write(requestBody);
        req.end();
      });

      const formattedResponse: LLMResponse = {
        id: data.id || `custom-${Date.now()}`,
        object: "chat.completion",
        created: data.created || Math.floor(Date.now() / 1000),
        model: this.actualModelName,
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: data.choices?.[0]?.message?.content || data.content || "",
              tool_calls: data.choices?.[0]?.message?.tool_calls || [],
            },
            finish_reason: data.choices?.[0]?.finish_reason || "stop",
          },
        ],
        usage: {
          prompt_tokens: data.usage?.prompt_tokens || 0,
          completion_tokens: data.usage?.completion_tokens || 0,
          total_tokens: data.usage?.total_tokens || 0,
        },
      };

      return formattedResponse as T;
    } catch (error) {
      logger({
        category: "custom-llm",
        level: 0,
        message: `Error: ${error instanceof Error ? error.message : String(error)}`,
      });

      if (retries > 0) {
        return this.createChatCompletion(options, logger || console, retries - 1);
      }
      throw error;
    }
  }
}
