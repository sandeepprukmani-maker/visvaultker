import OpenAI from "openai";
import { getAccessToken } from "./oauth";

async function createOpenAIClient(): Promise<OpenAI> {
  const token = await getAccessToken();
  const baseUrl = process.env.GW_BASE_URL || "https://api.openai.com/v1";
  
  return new OpenAI({
    apiKey: token,
    baseURL: baseUrl,
  });
}

export interface PageAnalysis {
  pageType: string;
  description: string;
  possibleActions: string[];
  keyElements: string[];
}

export interface AutomationPlan {
  steps: AutomationStep[];
  estimatedDuration: number;
  confidence: number;
}

export interface AutomationStep {
  action: string;
  selector?: string;
  xpath?: string;
  textSelector?: string;
  value?: string;
  description: string;
  waitBefore?: number;
  retryCount?: number;
  fallbackSelectors?: string[];
}

export interface VisualAnalysis {
  elements: Array<{
    description: string;
    location: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
    type: string;
    text?: string;
  }>;
  layout: string;
  suggestions: string[];
}

export interface ScreenshotComparison {
  changeDetected: boolean;
  changedRegions: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    description: string;
  }>;
  similarityScore: number;
  summary: string;
}

export class OpenAIService {
  async generateEmbedding(text: string): Promise<number[]> {
    try {
      const openai = await createOpenAIClient();
      const response = await openai.embeddings.create({
        model: "text-embedding-3-small",
        input: text,
      });
      return response.data[0].embedding;
    } catch (error) {
      console.error("Error generating embedding:", error);
      throw error;
    }
  }

  async analyzePage(pageData: {
    url: string;
    title: string;
    elements: Array<{ tag: string; text?: string; selector: string }>;
  }): Promise<PageAnalysis> {
    try {
      const elementsDescription = pageData.elements
        .slice(0, 50)
        .map((el) => `<${el.tag}>${el.text || ""}</${el.tag}>`)
        .join("\n");

      const prompt = `Analyze this web page and provide semantic understanding:

URL: ${pageData.url}
Title: ${pageData.title}

Key Elements:
${elementsDescription}

Provide a JSON response with:
1. pageType: A concise label (e.g., "Login Page", "Dashboard", "User Profile")
2. description: Brief description of the page's purpose
3. possibleActions: Array of common actions users might perform here
4. keyElements: Array of the most important UI elements on the page

Respond only with valid JSON, no markdown formatting.`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content:
              "You are a web page analyzer. Analyze web pages and identify their purpose, type, and key interactive elements. Always respond with valid JSON only.",
          },
          { role: "user", content: prompt },
        ],
        temperature: 0.3,
        response_format: { type: "json_object" },
      });

      const analysis = JSON.parse(
        response.choices[0].message.content || "{}"
      );
      return {
        pageType: analysis.pageType || "Unknown Page",
        description: analysis.description || "",
        possibleActions: analysis.possibleActions || [],
        keyElements: analysis.keyElements || [],
      };
    } catch (error) {
      console.error("Error analyzing page:", error);
      return {
        pageType: "Unknown Page",
        description: "Unable to analyze page",
        possibleActions: [],
        keyElements: [],
      };
    }
  }

  async analyzeScreenshot(screenshotBase64: string, query?: string): Promise<VisualAnalysis> {
    try {
      const prompt = query 
        ? `Analyze this screenshot and answer: ${query}\n\nProvide JSON with: elements (array of detected UI elements with location), layout (description), suggestions (improvement ideas).`
        : `Analyze this screenshot and identify all interactive UI elements.\n\nProvide JSON with:\n1. elements: Array of objects with {description, location: {x, y, width, height}, type, text}\n2. layout: Overall layout description\n3. suggestions: Array of accessibility/usability suggestions`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: "You are an expert UI/UX analyzer. Analyze screenshots to identify elements, layout patterns, and provide actionable insights. Always respond with valid JSON.",
          },
          {
            role: "user",
            content: [
              { type: "text", text: prompt },
              {
                type: "image_url",
                image_url: {
                  url: screenshotBase64,
                  detail: "high",
                },
              },
            ],
          },
        ],
        temperature: 0.2,
        response_format: { type: "json_object" },
        max_tokens: 4096,
      });

      const analysis = JSON.parse(response.choices[0].message.content || "{}");
      return {
        elements: analysis.elements || [],
        layout: analysis.layout || "Unable to analyze layout",
        suggestions: analysis.suggestions || [],
      };
    } catch (error) {
      console.error("Error analyzing screenshot:", error);
      return {
        elements: [],
        layout: "Unable to analyze",
        suggestions: [],
      };
    }
  }

  async compareScreenshots(
    screenshot1: string,
    screenshot2: string
  ): Promise<ScreenshotComparison> {
    try {
      const prompt = `Compare these two screenshots and identify what changed.\n\nProvide JSON with:\n1. changeDetected: boolean\n2. changedRegions: Array of {x, y, width, height, description} for changed areas\n3. similarityScore: 0-100 percentage\n4. summary: Brief description of changes`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: "You are a visual comparison expert. Compare screenshots to detect changes, new elements, removed elements, and layout shifts. Always respond with valid JSON.",
          },
          {
            role: "user",
            content: [
              { type: "text", text: prompt },
              {
                type: "image_url",
                image_url: { url: screenshot1, detail: "high" },
              },
              {
                type: "image_url",
                image_url: { url: screenshot2, detail: "high" },
              },
            ],
          },
        ],
        temperature: 0.1,
        response_format: { type: "json_object" },
        max_tokens: 2048,
      });

      const comparison = JSON.parse(response.choices[0].message.content || "{}");
      return {
        changeDetected: comparison.changeDetected || false,
        changedRegions: comparison.changedRegions || [],
        similarityScore: comparison.similarityScore || 0,
        summary: comparison.summary || "No changes detected",
      };
    } catch (error) {
      console.error("Error comparing screenshots:", error);
      return {
        changeDetected: false,
        changedRegions: [],
        similarityScore: 0,
        summary: "Unable to compare screenshots",
      };
    }
  }

  async findElementByVisual(
    screenshotBase64: string,
    description: string
  ): Promise<{ x: number; y: number; width: number; height: number } | null> {
    try {
      const prompt = `Find the UI element that matches: "${description}"\n\nProvide JSON with the element's location: {found: boolean, x: number, y: number, width: number, height: number}`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: "You are a visual element locator. Find UI elements in screenshots based on descriptions. Return coordinates as percentages (0-100) of image dimensions. Always respond with valid JSON.",
          },
          {
            role: "user",
            content: [
              { type: "text", text: prompt },
              {
                type: "image_url",
                image_url: { url: screenshotBase64, detail: "high" },
              },
            ],
          },
        ],
        temperature: 0.1,
        response_format: { type: "json_object" },
      });

      const result = JSON.parse(response.choices[0].message.content || "{}");
      if (result.found) {
        return {
          x: result.x || 0,
          y: result.y || 0,
          width: result.width || 0,
          height: result.height || 0,
        };
      }
      return null;
    } catch (error) {
      console.error("Error finding element by visual:", error);
      return null;
    }
  }

  async generateAutomationPlan(
    command: string,
    availablePages: Array<{
      url: string;
      title: string;
      pageType: string;
      elements: Array<{ tag: string; text?: string; selector: string; xpath?: string }>;
    }>
  ): Promise<AutomationPlan> {
    try {
      const pagesContext = availablePages
        .map(
          (page) =>
            `Page: ${page.title} (${page.url})
Type: ${page.pageType}
Elements: ${page.elements
              .slice(0, 20)
              .map((el) => `${el.tag}${el.text ? `: "${el.text}"` : ""} [CSS: ${el.selector}${el.xpath ? `, XPath: ${el.xpath}` : ''}]`)
              .join(", ")}`
        )
        .join("\n\n");

      const prompt = `You are an intelligent automation assistant. Convert this natural language command into a detailed automation plan.

Command: "${command}"

Available Pages and Elements:
${pagesContext}

Create a step-by-step automation plan. Each step should include:
- action: The type of action (navigate, click, type, select, wait, verify, waitForElement, scroll, hover, pressKey)
- selector: CSS selector for the element (if applicable)
- xpath: XPath selector as fallback (if applicable)
- textSelector: Text-based selector (if applicable)
- value: Value to input (for 'type' or 'select' actions)
- description: Human-readable description of what this step does
- waitBefore: Milliseconds to wait before this action (optional)
- retryCount: Number of times to retry if action fails (optional, default 3)
- fallbackSelectors: Array of alternative selectors to try if primary fails (optional)

Provide a JSON response with:
1. steps: Array of automation steps
2. estimatedDuration: Estimated time in seconds
3. confidence: Confidence level (0-100) that this plan will succeed

Important:
- Use the actual selectors from the available elements
- Provide multiple selector strategies (CSS, XPath, text) when possible
- For "Login" commands, find the login page, username/password fields, and submit button
- For "Add" or "Create" commands, navigate to the appropriate form and fill required fields
- For "Search" commands, find the search input and submit
- For "Delete" commands, find the item and its delete button
- Always verify success after critical actions
- Use waitForElement before interacting with dynamic content
- Add appropriate wait times for network requests and animations

Respond only with valid JSON, no markdown formatting.`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content:
              "You are an expert at creating robust web automation plans. You understand web UI patterns, dynamic content, and can convert natural language into precise automation steps with fallback strategies. Always respond with valid JSON only.",
          },
          { role: "user", content: prompt },
        ],
        temperature: 0.2,
        response_format: { type: "json_object" },
      });

      const plan = JSON.parse(response.choices[0].message.content || "{}");
      return {
        steps: plan.steps || [],
        estimatedDuration: plan.estimatedDuration || 10,
        confidence: plan.confidence || 50,
      };
    } catch (error) {
      console.error("Error generating automation plan:", error);
      throw error;
    }
  }

  async findSimilarElements(
    query: string,
    elements: Array<{
      id: string;
      tag: string;
      text?: string;
      selector: string;
      embedding?: string;
    }>
  ): Promise<Array<{ id: string; similarity: number }>> {
    try {
      const queryEmbedding = await this.generateEmbedding(query);

      const similarities = elements
        .filter((el) => el.embedding)
        .map((el) => {
          const elementEmbedding = JSON.parse(el.embedding!);
          const similarity = this.cosineSimilarity(
            queryEmbedding,
            elementEmbedding
          );
          return { id: el.id, similarity };
        })
        .sort((a, b) => b.similarity - a.similarity);

      return similarities.slice(0, 10);
    } catch (error) {
      console.error("Error finding similar elements:", error);
      return [];
    }
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) return 0;

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  async generateSmartSelectors(
    elementDescription: string,
    pageContext: {
      url: string;
      elements: Array<{ tag: string; text?: string; attributes: Record<string, string> }>;
    }
  ): Promise<{
    cssSelector?: string;
    xpath?: string;
    textSelector?: string;
    ariaSelector?: string;
    confidence: number;
  }> {
    try {
      const elementsContext = pageContext.elements
        .slice(0, 30)
        .map((el) => `${el.tag}: ${el.text || ''} ${JSON.stringify(el.attributes)}`)
        .join('\n');

      const prompt = `Given this page context and element description, generate multiple robust selectors.

Element Description: "${elementDescription}"

Page Elements:
${elementsContext}

Provide JSON with:
1. cssSelector: CSS selector (preferably using stable attributes like id, data-testid, aria-label)
2. xpath: XPath selector
3. textSelector: Text-based selector
4. ariaSelector: ARIA-based selector if applicable
5. confidence: 0-100 confidence that these selectors will work

Prefer stable selectors over fragile ones. Avoid relying on dynamic classes or nth-child when possible.`;

      const openai = await createOpenAIClient();
      const response = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: "You are a selector generation expert. Create robust, maintainable selectors that resist UI changes. Always respond with valid JSON.",
          },
          { role: "user", content: prompt },
        ],
        temperature: 0.1,
        response_format: { type: "json_object" },
      });

      const result = JSON.parse(response.choices[0].message.content || "{}");
      return {
        cssSelector: result.cssSelector,
        xpath: result.xpath,
        textSelector: result.textSelector,
        ariaSelector: result.ariaSelector,
        confidence: result.confidence || 50,
      };
    } catch (error) {
      console.error("Error generating smart selectors:", error);
      return { confidence: 0 };
    }
  }
}

export const openAIService = new OpenAIService();
