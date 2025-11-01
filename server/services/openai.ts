import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

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
  value?: string;
  description: string;
}

export class OpenAIService {
  /**
   * Generate embeddings for text content
   */
  async generateEmbedding(text: string): Promise<number[]> {
    try {
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

  /**
   * Analyze a page's content and structure to understand its purpose
   */
  async analyzePage(pageData: {
    url: string;
    title: string;
    elements: Array<{ tag: string; text?: string; selector: string }>;
  }): Promise<PageAnalysis> {
    try {
      const elementsDescription = pageData.elements
        .slice(0, 50) // Limit to first 50 elements to save tokens
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

  /**
   * Convert a natural language command into a structured automation plan
   */
  async generateAutomationPlan(
    command: string,
    availablePages: Array<{
      url: string;
      title: string;
      pageType: string;
      elements: Array<{ tag: string; text?: string; selector: string }>;
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
              .map((el) => `${el.tag}${el.text ? `: "${el.text}"` : ""} [${el.selector}]`)
              .join(", ")}`
        )
        .join("\n\n");

      const prompt = `You are an intelligent automation assistant. Convert this natural language command into a detailed automation plan.

Command: "${command}"

Available Pages and Elements:
${pagesContext}

Create a step-by-step automation plan. Each step should include:
- action: The type of action (navigate, click, type, select, wait, verify)
- selector: CSS selector for the element (if applicable)
- value: Value to input (for 'type' or 'select' actions)
- description: Human-readable description of what this step does

Provide a JSON response with:
1. steps: Array of automation steps
2. estimatedDuration: Estimated time in seconds
3. confidence: Confidence level (0-100) that this plan will succeed

Important:
- Use the actual selectors from the available elements
- For "Login" commands, find the login page, username/password fields, and submit button
- For "Add" or "Create" commands, navigate to the appropriate form and fill required fields
- For "Search" commands, find the search input and submit
- For "Delete" commands, find the item and its delete button
- Always verify success after critical actions

Respond only with valid JSON, no markdown formatting.`;

      const response = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content:
              "You are an expert at creating web automation plans. You understand web UI patterns and can convert natural language into precise automation steps. Always respond with valid JSON only.",
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

  /**
   * Find the most similar elements based on semantic search
   */
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
      // Generate embedding for query
      const queryEmbedding = await this.generateEmbedding(query);

      // Calculate cosine similarity for each element
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

      return similarities.slice(0, 10); // Return top 10 matches
    } catch (error) {
      console.error("Error finding similar elements:", error);
      return [];
    }
  }

  /**
   * Calculate cosine similarity between two vectors
   */
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
}

export const openAIService = new OpenAIService();
