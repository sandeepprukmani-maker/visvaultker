import { z } from "zod";
import type { AutomationMode } from "@shared/schema";

interface ParsedPrompt {
  url: string;
  task: string;
  suggestedMode: AutomationMode;
  reasoning: string;
}

/**
 * Extract URL from natural language prompt
 */
export function extractUrl(prompt: string): string | null {
  // Match common URL patterns
  const urlRegex = /(https?:\/\/[^\s]+)/gi;
  const matches = prompt.match(urlRegex);
  
  if (matches && matches.length > 0) {
    return matches[0].replace(/[,;.]$/, ''); // Remove trailing punctuation
  }
  
  // Try to find domain-like patterns without protocol
  const domainRegex = /(?:go to |visit |open |navigate to |on )?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?)/gi;
  const domainMatches = prompt.match(domainRegex);
  
  if (domainMatches && domainMatches.length > 0) {
    let domain = domainMatches[0]
      .replace(/^(?:go to |visit |open |navigate to |on )/i, '')
      .replace(/[,;.]$/, '');
    
    // Add https:// if not present
    if (!domain.startsWith('http://') && !domain.startsWith('https://')) {
      domain = 'https://' + domain;
    }
    
    return domain;
  }
  
  return null;
}

/**
 * Analyze prompt to determine the best automation mode
 */
export function suggestMode(prompt: string): {
  mode: AutomationMode;
  reasoning: string;
} {
  const lowerPrompt = prompt.toLowerCase();
  
  // Extract keywords
  const hasExtractKeywords = /extract|get|scrape|pull|grab|fetch|find data|retrieve/i.test(lowerPrompt);
  const hasObserveKeywords = /find|locate|check if|see|show|list|discover/i.test(lowerPrompt);
  const hasActKeywords = /click|type|fill|enter|submit|scroll|press|select|choose/i.test(lowerPrompt);
  const hasMultiStep = /and then|after|next|finally|then|complete|workflow|process/i.test(lowerPrompt);
  
  // Decision logic
  if (hasMultiStep || (hasActKeywords && hasExtractKeywords)) {
    return {
      mode: "agent",
      reasoning: "Detected multi-step workflow requiring autonomous execution"
    };
  }
  
  if (hasExtractKeywords && !hasActKeywords) {
    return {
      mode: "extract",
      reasoning: "Detected data extraction request"
    };
  }
  
  if (hasObserveKeywords && !hasActKeywords && !hasExtractKeywords) {
    return {
      mode: "observe",
      reasoning: "Detected element discovery request"
    };
  }
  
  if (hasActKeywords) {
    return {
      mode: "act",
      reasoning: "Detected single action request"
    };
  }
  
  // Default to agent for complex requests
  return {
    mode: "agent",
    reasoning: "Using agent mode for flexible task execution"
  };
}

/**
 * Parse natural language prompt into structured automation request
 */
export function parsePrompt(prompt: string): ParsedPrompt {
  const url = extractUrl(prompt);
  
  if (!url) {
    throw new Error(
      "Could not detect a URL in your prompt. Please include a website URL (e.g., 'https://example.com' or 'go to example.com')"
    );
  }
  
  // Remove the URL from the task description
  const task = prompt
    .replace(url, '')
    .replace(/^(?:go to |visit |open |navigate to |on )\s*/i, '')
    .trim();
  
  const { mode, reasoning } = suggestMode(prompt);
  
  return {
    url,
    task: task || "Complete the automation task",
    suggestedMode: mode,
    reasoning,
  };
}

/**
 * Generate appropriate code based on the mode used
 */
export function generateCodeForMode(
  mode: AutomationMode,
  url: string,
  task: string,
  model: string
): string {
  const baseSetup = `import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod";

const stagehand = new Stagehand({
  env: "BROWSERBASE",
  model: {
    modelName: "${model}",
    apiKey: process.env.CUSTOM_MODEL_API_KEY || process.env.GOOGLE_AI_API_KEY,
    baseURL: process.env.CUSTOM_MODEL_BASE_URL || process.env.GW_BASE_URL
  },
  enableCaching: true
});

await stagehand.init();
const page = stagehand.context.pages()[0];

await page.goto("${url}");`;

  switch (mode) {
    case "act":
      return `${baseSetup}

// Execute action
await page.act("${task}");

await stagehand.close();`;

    case "observe":
      return `${baseSetup}

// Discover elements
const elements = await page.observe("${task}");
console.log("Found elements:", elements);

await stagehand.close();`;

    case "extract":
      return `${baseSetup}

// Extract data
const data = await page.extract({
  instruction: "${task}",
  schema: z.object({
    // Define your schema here
    data: z.string()
  })
});

console.log("Extracted data:", data);

await stagehand.close();`;

    case "agent":
      return `${baseSetup}

// Execute multi-step workflow
const agent = stagehand.agent({
  cua: true,
  model: "${model}",
  systemPrompt: "You are a helpful automation assistant."
});

const result = await agent.execute({
  instruction: "${task}",
  maxSteps: 20
});

console.log("Result:", result.message);
console.log("Completed:", result.completed);

await stagehand.close();`;

    default:
      return baseSetup + "\n\nawait stagehand.close();";
  }
}
