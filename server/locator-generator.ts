import { LogEntry } from "@shared/schema";

export interface StagehandStep {
  action: "click" | "fill" | "type" | "press" | "goto" | "extract" | "observe" | "scroll";
  selector?: string; // XPath from Stagehand observe
  iframeChain?: string[]; // Array of iframe selectors
  parameters?: {
    value?: string;
    text?: string;
    key?: string;
  };
  description?: string;
}

export interface LocatorCodeOptions {
  url: string;
  model: string;
  mode: string;
  steps: StagehandStep[];
  cacheDir?: string;
}

/**
 * Normalize Stagehand result or log entry into a structured step
 */
export function normalizeStep(
  action: string,
  selector?: string,
  description?: string,
  value?: string
): StagehandStep {
  // Detect if selector contains iframe references
  const iframeChain: string[] = [];
  let finalSelector = selector;

  if (selector) {
    // Check for iframe in XPath (e.g., //iframe[@id='widget']//button)
    const iframeMatches = selector.match(/\/\/iframe(?:\[@[^\]]+\])?/g);
    if (iframeMatches) {
      // Extract iframe selectors - keep full XPath with // prefix
      const parts = selector.split(/\/\/iframe(?:\[@[^\]]+\])?/);
      for (let i = 0; i < iframeMatches.length; i++) {
        // Keep the full XPath including // prefix
        iframeChain.push(iframeMatches[i]); // e.g., "//iframe[@id='widget']"
      }
      // Last part is the final selector - ensure it has // prefix if it's XPath
      const lastPart = parts[parts.length - 1];
      finalSelector = lastPart.startsWith('/') ? lastPart : `//${lastPart}`;
    }
  }

  // Determine action type from description or action string
  let actionType: StagehandStep["action"] = "click";
  const lowerAction = action.toLowerCase();
  
  if (lowerAction.includes("fill") || lowerAction.includes("type") || lowerAction.includes("enter")) {
    actionType = value ? "fill" : "type";
  } else if (lowerAction.includes("press")) {
    actionType = "press";
  } else if (lowerAction.includes("navigate") || lowerAction.includes("goto")) {
    actionType = "goto";
  } else if (lowerAction.includes("extract")) {
    actionType = "extract";
  } else if (lowerAction.includes("observe") || lowerAction.includes("find")) {
    actionType = "observe";
  } else if (lowerAction.includes("scroll")) {
    actionType = "scroll";
  }

  return {
    action: actionType,
    selector: finalSelector,
    iframeChain: iframeChain.length > 0 ? iframeChain : undefined,
    parameters: value ? { value, text: value } : undefined,
    description,
  };
}

/**
 * Escape string for safe interpolation in TypeScript code
 */
function escapeForTypeScript(str: string): string {
  return str
    .replace(/\\/g, '\\\\')  // Escape backslashes
    .replace(/"/g, '\\"')     // Escape double quotes
    .replace(/'/g, "\\'")     // Escape single quotes
    .replace(/`/g, '\\`')     // Escape backticks
    .replace(/\n/g, '\\n')    // Escape newlines
    .replace(/\r/g, '\\r')    // Escape carriage returns
    .replace(/\t/g, '\\t');   // Escape tabs
}

/**
 * Generate locator code from selector and iframe chain
 */
function generateLocatorCall(step: StagehandStep): string {
  if (!step.selector) {
    return '';
  }

  // Escape the selector for safe interpolation
  const escapedSelector = escapeForTypeScript(step.selector);
  
  if (step.iframeChain && step.iframeChain.length > 0) {
    // Use deepLocator for iframe elements with XPath
    // Each iframe needs xpath= prefix, and the final selector too
    const iframeXPaths = step.iframeChain.map(iframe => `xpath=${escapeForTypeScript(iframe)}`);
    const finalXPath = `xpath=${escapedSelector}`;
    const deepLocatorPath = [...iframeXPaths, finalXPath].join(' >> ');
    return `page.deepLocator("${deepLocatorPath}")`;
  } else {
    // Use regular locator with XPath syntax (xpath=...)
    // Playwright understands xpath= prefix for XPath selectors
    return `page.locator("xpath=${escapedSelector}")`;
  }
}

/**
 * Generate action code from step
 */
function generateActionCode(step: StagehandStep, indent: string = ''): string {
  const locatorCall = generateLocatorCall(step);
  
  if (!locatorCall) {
    // No selector-based action
    if (step.action === 'goto') {
      return `${indent}// Navigate is handled in initialization`;
    }
    const safeDescription = step.description ? escapeForTypeScript(step.description) : 'Unknown action';
    return `${indent}// ${safeDescription}`;
  }

  const comment = step.description ? `${indent}// ${escapeForTypeScript(step.description)}\n` : '';
  
  switch (step.action) {
    case 'click':
      return `${comment}${indent}await ${locatorCall}.click();`;
    
    case 'fill':
      const fillValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${comment}${indent}await ${locatorCall}.fill("${fillValue}");`;
    
    case 'type':
      const typeValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${comment}${indent}await ${locatorCall}.type("${typeValue}");`;
    
    case 'press':
      const key = escapeForTypeScript(step.parameters?.key || 'Enter');
      return `${comment}${indent}await ${locatorCall}.press("${key}");`;
    
    case 'scroll':
      return `${comment}${indent}await ${locatorCall}.scrollIntoViewIfNeeded();`;
    
    default:
      return `${comment}${indent}// Unsupported action: ${step.action}`;
  }
}

/**
 * Generate complete TypeScript code with locators
 */
export function emitLocatorScript(options: LocatorCodeOptions): string {
  const { url, model, mode, steps, cacheDir } = options;
  
  const imports = [
    `import { Stagehand } from "@browserbasehq/stagehand";`,
  ];
  
  // Add Zod import if needed for extract mode
  if (mode === 'extract' || steps.some(s => s.action === 'extract')) {
    imports.push(`import { z } from "zod";`);
  }

  const cacheDirConfig = cacheDir ? `\n  cacheDir: "${escapeForTypeScript(cacheDir)}",` : '';
  const escapedUrl = escapeForTypeScript(url);
  const escapedModel = escapeForTypeScript(model);
  
  const setupCode = `
const stagehand = new Stagehand({
  env: "BROWSERBASE",
  model: {
    modelName: "${escapedModel}",
    apiKey: process.env.CUSTOM_MODEL_API_KEY || process.env.GOOGLE_AI_API_KEY,
    baseURL: process.env.CUSTOM_MODEL_BASE_URL || process.env.GW_BASE_URL
  },
  enableCaching: true,${cacheDirConfig}
});

await stagehand.init();
const page = stagehand.context.pages()[0];

// Navigate to the target URL
await page.goto("${escapedUrl}", { waitUntil: "networkidle" });
`;

  // Generate action code for each step
  const actionCodes = steps
    .filter(step => step.action !== 'goto') // Skip goto as it's in setup
    .map(step => generateActionCode(step, ''))
    .filter(code => code.trim().length > 0);

  const cleanupCode = `
// Close the browser
await stagehand.close();
`;

  const fullCode = `${imports.join('\n')}

${setupCode}
${actionCodes.join('\n\n')}
${cleanupCode}`;

  return fullCode.trim();
}

/**
 * Generate cached version of code (using Stagehand's caching with cacheDir)
 */
export function emitCachedScript(options: LocatorCodeOptions): string {
  const cacheDirSuffix = options.mode === 'agent' ? '-agent' : '-actions';
  const cacheDir = options.cacheDir || `./cache/${options.mode}${cacheDirSuffix}`;
  
  return emitLocatorScript({
    ...options,
    cacheDir,
  });
}
