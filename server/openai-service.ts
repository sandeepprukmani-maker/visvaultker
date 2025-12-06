import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface BrowserActionPlan {
  actions: {
    tool: string;
    args: Record<string, string>;
    description: string;
  }[];
  explanation: string;
}

const SYSTEM_PROMPT = `You are a browser automation assistant that helps users automate web tasks using Playwright MCP.
Your job is to convert natural language requests into a sequence of browser actions.

Available browser actions (MCP tools):
- browser_navigate: Navigate to a URL. Args: { "url": "https://example.com" }
- browser_click: Click an element. Args: { "element": "button text or element description", "ref": "optional element reference" }
- browser_type: Type text into element. Args: { "element": "input description", "text": "text to type", "ref": "optional element reference", "submit": "true/false" }
- browser_take_screenshot: Take a screenshot. Args: { "raw": "true/false" }
- browser_snapshot: Get page accessibility snapshot. Args: {}
- browser_select_option: Select from dropdown. Args: { "element": "select description", "values": ["option values"], "ref": "optional element reference" }
- browser_hover: Hover over element. Args: { "element": "element description", "ref": "optional element reference" }
- browser_evaluate: Execute JavaScript. Args: { "expression": "code to run" }
- browser_press_key: Press a key. Args: { "key": "Enter/Tab/Escape/etc" }
- browser_fill_form: Fill form fields. Args: { "element": "form description", "values": {"field1": "value1"} }

Guidelines:
1. Break down complex tasks into simple, sequential steps
2. Always start with browser_navigate if the user mentions a URL or website
3. Use descriptive element selectors based on visible text, labels, or attributes
4. For search inputs, use browser_type with submit: "true" to press Enter after typing
5. Keep actions atomic and focused
6. If searching Google, navigate to google.com first, then type in the search box

Respond with a JSON object in this format:
{
  "actions": [
    { "tool": "browser_navigate", "args": { "url": "https://google.com" }, "description": "Navigate to Google" },
    { "tool": "browser_type", "args": { "element": "Search textarea", "text": "weather", "submit": "true" }, "description": "Type search query and submit" }
  ],
  "explanation": "Brief explanation of what these actions will do"
}`;

export async function planBrowserActions(prompt: string): Promise<BrowserActionPlan> {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: prompt },
      ],
      response_format: { type: "json_object" },
      max_tokens: 2048,
    });

    const content = response.choices[0].message.content;
    if (!content) {
      throw new Error("No response from OpenAI");
    }

    const plan = JSON.parse(content) as BrowserActionPlan;
    
    if (!plan.actions || !Array.isArray(plan.actions)) {
      throw new Error("Invalid action plan format");
    }

    return plan;
  } catch (error) {
    console.error("Error planning browser actions:", error);
    if (error instanceof Error && error.message.includes("quota")) {
      throw new Error("API quota exceeded. Please check your OpenAI billing settings.");
    }
    throw new Error(`Failed to plan actions: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

export async function summarizeResult(
  prompt: string,
  actions: { tool: string; result: unknown; error?: string }[]
): Promise<string> {
  try {
    const actionSummary = actions
      .map((a) => {
        if (a.error) {
          return `- ${a.tool}: ERROR - ${a.error}`;
        }
        const resultStr = typeof a.result === "string" 
          ? a.result.slice(0, 500) 
          : JSON.stringify(a.result).slice(0, 500);
        return `- ${a.tool}: ${resultStr}`;
      })
      .join("\n");

    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that summarizes browser automation results. Be concise and focus on what was accomplished or what went wrong.",
        },
        {
          role: "user",
          content: `User request: ${prompt}\n\nActions performed:\n${actionSummary}\n\nProvide a brief, user-friendly summary of what happened.`,
        },
      ],
      max_tokens: 512,
    });

    return response.choices[0].message.content || "Automation completed.";
  } catch (error) {
    console.error("Error summarizing result:", error);
    return "Automation completed. Check the action log for details.";
  }
}
