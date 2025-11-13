import { spawn } from "child_process";
import { LLMClient, CreateChatCompletionOptions, LLMResponse, AvailableModel } from "@browserbasehq/stagehand";
import https from "https";

export class CustomLLMClient extends LLMClient {
    type = "custom";
    private apiEndpoint: string;
    private actualModelName: string;
    private cachedToken: string | null = null;
    private tokenExpiry: number = 0;

    constructor({
        modelName = "gpt-4o" as AvailableModel,
        apiEndpoint,
        actualModelName = "gpt-4o-1-2025-04-14-eastus-dz",
    }: {
        modelName?: AvailableModel;
        apiEndpoint: string;
        actualModelName?: string;
    }) {
        super(modelName);
        this.type = "custom";
        this.apiEndpoint = apiEndpoint;
        this.actualModelName = actualModelName;
        this.hasVision = false;
    }

    private async getToken(): Promise<string> {
        const now = Date.now();
        
        if (this.cachedToken && this.tokenExpiry > now) {
            return this.cachedToken;
        }

        const tokenData = await this.fetchOAuthConfig();
        const accessToken = tokenData.access_token;
        
        if (typeof accessToken !== "string" || !accessToken) {
            throw new Error("OAuth token is invalid or missing");
        }
        
        this.cachedToken = accessToken;
        
        if (tokenData.expires_in) {
            this.tokenExpiry = now + (tokenData.expires_in * 1000) - 60000;
        } else {
            this.tokenExpiry = now + 3600000;
        }

        return accessToken;
    }

    async createChatCompletion<T = LLMResponse & { usage?: LLMResponse["usage"] }>(
        createOptions: CreateChatCompletionOptions
    ): Promise<T> {
        const { messages, temperature, maxTokens, response_model } = createOptions.options;
        let retries = createOptions.retries ?? 3;
        let logger = createOptions.logger;

        try {
            const token = await this.getToken();
            
            const requestPayload: any = {
                model: this.actualModelName,
                messages: messages.map(msg => ({
                    role: msg.role,
                    content: typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content),
                })),
                temperature,
                max_tokens: maxTokens,
            };

            const requestBody = JSON.stringify(requestPayload);

            const data = await new Promise<any>((resolve, reject) => {
                try {
                    const url = new URL(this.apiEndpoint);

                    const options = {
                        hostname: url.hostname,
                        port: url.port || 443,
                        path: url.pathname + url.search,
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${token}`,
                            "Content-Length": Buffer.byteLength(requestBody),
                        },
                    };

                    const req = https.request(options, (res) => {
                        let responseData = "";
                        res.on("data", (chunk) => {
                            responseData += chunk;
                        });

                        res.on("end", () => {
                            if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
                                try {
                                    const parsed = JSON.parse(responseData);
                                    resolve(parsed);
                                } catch (e) {
                                    reject(new Error(`Failed to parse response: ${responseData}`));
                                }
                            } else {
                                reject(new Error(`API request failed with status ${res.statusCode}: ${responseData}`));
                            }
                        });
                    });

                    req.on("error", (error) => {
                        reject(error);
                    });

                    req.write(requestBody);
                    req.end();
                } catch (error) {
                    logger({
                        category: "custom-llm",
                        message: `Error creating request: ${(error instanceof Error ? error.message : String(error))}`,
                        level: 0,
                    });
                    reject(error);
                }
            });

            const messageContent = data.choices?.[0]?.message?.content || data.content || "";
            const toolCalls = data.choices?.[0]?.message?.tool_calls;

            const messageObj: any = {
                role: "assistant",
                content: messageContent,
            };
            if (toolCalls && Array.isArray(toolCalls) && toolCalls.length > 0) {
                messageObj.tool_calls = toolCalls;
            }

            const formattedResponse: LLMResponse = {
                id: `custom-${Date.now()}`,
                object: "chat.completion",
                created: Math.floor(Date.now() / 1000),
                model: this.actualModelName,
                choices: [
                    {
                        index: 0,
                        message: messageObj,
                        finish_reason: data.choices?.[0]?.finish_reason || "stop",
                    },
                ],
                usage: {
                    prompt_tokens: data.usage?.prompt_tokens || 0,
                    completion_tokens: data.usage?.completion_tokens || 0,
                    total_tokens: data.usage?.total_tokens || 0,
                },
            };

            if (response_model) {
                logger({
                    category: "custom-llm",
                    message: `Response model requested, parsing: ${messageContent}`,
                    level: 1,
                });
                try {
                    const parsedData = JSON.parse(messageContent);
                    logger({
                        category: "custom-llm",
                        message: `Parsed ${JSON.stringify(parsedData, null, 2)}`,
                        level: 1,
                    });
                    if (parsedData && typeof parsedData === "object") {
                        if (parsedData.element && parsedData.action) {
                            const elementId = parsedData.element.id?.replace(/[^\[\]1]/g, "") || "0-1";
                            const normalizedData = {
                                elementId,
                                method: parsedData.action,
                                arguments: parsedData.argument ? [parsedData.argument] : (parsedData.arguments || []),
                            };
                            logger({
                                category: "custom-llm",
                                message: `Normalized data (element/action format): ${JSON.stringify(normalizedData, null, 2)}`,
                                level: 1,
                            });
                            return {
                                ...normalizedData,
                                usage: formattedResponse.usage,
                            } as T;
                        }
                        if (parsedData.elementId && parsedData.action) {
                            const normalizedData = {
                                elementId: parsedData.elementId,
                                method: parsedData.action,
                                arguments: parsedData.argument ? [parsedData.argument] : (parsedData.arguments || []),
                            };
                            logger({
                                category: "custom-llm",
                                message: `Normalized data (elementId/action format): ${JSON.stringify(normalizedData, null, 2)}`,
                                level: 1,
                            });
                            return {
                                ...normalizedData,
                                usage: formattedResponse.usage,
                            } as T;
                        }
                    }
                    return {
                        ...parsedData,
                        usage: formattedResponse.usage,
                    } as T;
                } catch (e) {
                    logger({
                        category: "custom-llm",
                        message: `Failed to parse JSON, attempting extraction: ${e instanceof Error ? e.message : String(e)}`,
                        level: 1,
                    });

                    const jsonMatch = messageContent.match(/[\[{][\s\S]*[\]}]/);
                    if (jsonMatch) {
                        try {
                            const extractedJson = JSON.parse(jsonMatch[0]);
                            logger({
                                category: "custom-llm",
                                message: `Extracted JSON: ${JSON.stringify(extractedJson, null, 2)}`,
                                level: 1,
                            });
                            if (extractedJson.element && extractedJson.action) {
                                const elementId = extractedJson.element.id?.replace(/[^\[\]1]/g, "") || "0-1";
                                const normalizedData = {
                                    elementId,
                                    method: extractedJson.action,
                                    arguments: extractedJson.argument ? [extractedJson.argument] : (extractedJson.arguments || []),
                                };
                                logger({
                                    category: "custom-llm",
                                    message: `Normalized data (extracted): ${JSON.stringify(normalizedData, null, 2)}`,
                                    level: 1,
                                });
                                return {
                                    ...normalizedData,
                                    usage: formattedResponse.usage,
                                } as T;
                            }
                            return {
                                ...extractedJson,
                                usage: formattedResponse.usage,
                            } as T;
                        } catch (e2) {
                            logger({
                                category: "custom-llm",
                                message: `Extraction also failed: ${e2 instanceof Error ? e2.message : String(e2)}`,
                                level: 1,
                            });
                        }
                    }
                }
            }

            return formattedResponse as T;
        } catch (error) {
            logger({
                category: "custom-llm",
                message: `Error: ${error instanceof Error ? error.message : String(error)}`,
                level: 0,
            });
            if (retries > 0) {
                return this.createChatCompletion({ 
                    options: createOptions.options, 
                    logger, 
                    retries: retries - 1 
                });
            }
            throw error;
        }
    }

    async fetchOAuthConfig(): Promise<any> {
        return new Promise((resolve, reject) => {
            const pythonProcess = spawn("python", ["fetch_token.py"]);
            let output = "";
            let errorOutput = "";
            pythonProcess.stdout.on("data", (data) => {
                output += data.toString();
            });
            pythonProcess.stderr.on("data", (data) => {
                errorOutput += data.toString();
            });
            pythonProcess.on("close", (code) => {
                if (code !== 0) {
                    reject(new Error(`Python script failed: ${errorOutput}`));
                } else {
                    try {
                        const result = JSON.parse(output.trim());
                        if (result.error) {
                            reject(new Error(`OAuth error: ${result.error}`));
                        } else {
                            resolve(result);
                        }
                    } catch (e) {
                        reject(new Error(`Failed to parse OAuth response: ${output}`));
                    }
                }
            });
        });
    }
}
