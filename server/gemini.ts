import { GoogleGenAI } from "@google/genai";

// DON'T DELETE THIS COMMENT
// Follow these instructions when using this blueprint:
// - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
//   - do not change this unless explicitly requested by the user

// This API key is from Gemini Developer API Key, not vertex AI API Key
const apiKey = process.env.GEMINI_API_KEY;

if (!apiKey) {
  console.error("⚠️  GEMINI_API_KEY is not set. AI-powered automation will not work.");
  console.error("Please set GEMINI_API_KEY in your environment variables.");
}

const ai = apiKey ? new GoogleGenAI({ apiKey }) : null;

export interface PlaywrightAction {
  action: string;
  code: string;
  description: string;
}

export interface AutomationPlan {
  actions: PlaywrightAction[];
  estimatedTokens: number;
}

/**
 * Convert natural language prompt to Playwright actions using Gemini
 * with optimized prompting for token efficiency
 */
export async function convertPromptToPlaywrightActions(
  userPrompt: string,
  pageContext?: string
): Promise<AutomationPlan> {
  // Check if AI is available
  if (!ai) {
    throw new Error("Gemini AI is not configured. Please set GEMINI_API_KEY environment variable.");
  }

  // Optimized system prompt with clear, concise instructions
  const systemPrompt = `You are a Playwright automation expert. Convert user requests into Playwright code actions.

Rules:
1. Return ONLY valid JavaScript/TypeScript Playwright code
2. Use page.goto(), page.click(), page.fill(), page.getByRole(), page.getByText(), etc.
3. Be specific with selectors - prefer getByRole() or getByText() over CSS selectors
4. Each action should be a single line of code
5. Include proper waits and error handling
6. Keep code minimal and efficient

Respond with JSON in this exact format:
{
  "actions": [
    {
      "action": "navigate",
      "code": "await page.goto('https://example.com');",
      "description": "Navigate to example.com"
    }
  ]
}`;

  let userMessage = `Convert this request to Playwright actions: "${userPrompt}"`;
  
  // Add page context if available (for follow-up actions on same page)
  if (pageContext) {
    userMessage += `\n\nCurrent page context:\n${pageContext}`;
  }

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash", // Fast model for quick response
      config: {
        systemInstruction: systemPrompt,
        responseMimeType: "application/json",
        responseSchema: {
          type: "object",
          properties: {
            actions: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  action: { type: "string" },
                  code: { type: "string" },
                  description: { type: "string" },
                },
                required: ["action", "code", "description"],
              },
            },
          },
          required: ["actions"],
        },
      },
      contents: userMessage,
    });

    const rawJson = response.text;
    
    if (!rawJson) {
      throw new Error("Empty response from Gemini");
    }

    const plan = JSON.parse(rawJson);
    
    // Estimate tokens used (rough approximation)
    const estimatedTokens = Math.ceil((systemPrompt.length + userMessage.length + rawJson.length) / 4);
    
    return {
      actions: plan.actions || [],
      estimatedTokens,
    };
  } catch (error) {
    console.error("Gemini error:", error);
    throw new Error(`Failed to convert prompt to Playwright actions: ${error}`);
  }
}

/**
 * Batch multiple prompts to reduce token usage
 * Combines multiple user requests into a single LLM call
 */
export async function batchPrompts(prompts: string[]): Promise<AutomationPlan> {
  // Check if AI is available
  if (!ai) {
    throw new Error("Gemini AI is not configured. Please set GEMINI_API_KEY environment variable.");
  }

  const systemPrompt = `You are a Playwright automation expert. Convert multiple user requests into a single efficient Playwright automation sequence.

Combine and optimize the actions to avoid redundant operations.`;

  const batchedPrompt = prompts.map((p, i) => `${i + 1}. ${p}`).join("\n");

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      config: {
        systemInstruction: systemPrompt,
        responseMimeType: "application/json",
        responseSchema: {
          type: "object",
          properties: {
            actions: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  action: { type: "string" },
                  code: { type: "string" },
                  description: { type: "string" },
                },
                required: ["action", "code", "description"],
              },
            },
          },
          required: ["actions"],
        },
      },
      contents: batchedPrompt,
    });

    const rawJson = response.text;
    
    if (!rawJson) {
      throw new Error("Empty response from Gemini");
    }

    const plan = JSON.parse(rawJson);
    const estimatedTokens = Math.ceil((systemPrompt.length + batchedPrompt.length + rawJson.length) / 4);
    
    return {
      actions: plan.actions || [],
      estimatedTokens,
    };
  } catch (error) {
    console.error("Gemini batching error:", error);
    throw new Error(`Failed to batch prompts: ${error}`);
  }
}
