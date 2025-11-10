import { LogEntry } from "@shared/schema";

export interface StagehandStep {
  action: "click" | "fill" | "type" | "press" | "goto" | "extract" | "observe" | "scroll" | "hover" | "select";
  selector?: string; // XPath or CSS selector from Stagehand observe
  iframeChain?: string[]; // Array of iframe selectors for deepLocator
  parameters?: {
    value?: string;
    text?: string;
    key?: string;
    variable?: string; // For sensitive data using %variable% pattern
    options?: string[]; // For select dropdowns
  };
  description?: string;
  useDeepLocator?: boolean; // Force deepLocator usage
}

export interface LocatorCodeOptions {
  url: string;
  model: string;
  mode: string;
  steps: StagehandStep[];
  cacheDir?: string;
  variables?: Record<string, string>; // For sensitive data variables
  includeMetrics?: boolean; // Track performance metrics
  includeHistory?: boolean; // Track operation history
  includeFallback?: boolean; // Include agent fallback pattern
}

/**
 * Normalize Stagehand result or log entry into a structured step
 * Follows Stagehand v3 best practices for locator generation
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
  let useDeepLocator = false;

  if (selector) {
    // Check for >> notation (deepLocator syntax)
    if (selector.includes(' >> ')) {
      useDeepLocator = true;
      const parts = selector.split(' >> ');
      // All but last are iframes
      iframeChain.push(...parts.slice(0, -1));
      finalSelector = parts[parts.length - 1];
    } 
    // Check for iframe in XPath (e.g., //iframe[@id='widget']//button)
    else {
      const iframeMatches = selector.match(/\/\/iframe(?:\[@[^\]]+\])?/g);
      if (iframeMatches) {
        useDeepLocator = true;
        // Extract iframe selectors - keep full XPath with // prefix
        const parts = selector.split(/\/\/iframe(?:\[@[^\]]+\])?/);
        for (let i = 0; i < iframeMatches.length; i++) {
          iframeChain.push(iframeMatches[i]);
        }
        // Last part is the final selector
        const lastPart = parts[parts.length - 1];
        finalSelector = lastPart.startsWith('/') ? lastPart : `//${lastPart}`;
      }
    }
  }

  // Determine action type from description or action string
  let actionType: StagehandStep["action"] = "click";
  const lowerAction = action.toLowerCase();
  
  if (lowerAction.includes("fill") || lowerAction.includes("enter") || lowerAction.includes("input")) {
    actionType = "fill";
  } else if (lowerAction.includes("type")) {
    actionType = "type";
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
  } else if (lowerAction.includes("hover")) {
    actionType = "hover";
  } else if (lowerAction.includes("select")) {
    actionType = "select";
  }

  // Check if value contains sensitive data pattern %variable%
  let variable: string | undefined;
  let cleanValue = value;
  
  if (value && value.includes('%')) {
    const variableMatch = value.match(/%([^%]+)%/);
    if (variableMatch) {
      variable = variableMatch[1];
      cleanValue = undefined; // Don't include actual value if it's a variable
    }
  }

  return {
    action: actionType,
    selector: finalSelector,
    iframeChain: iframeChain.length > 0 ? iframeChain : undefined,
    useDeepLocator,
    parameters: {
      value: cleanValue,
      text: cleanValue,
      variable,
    },
    description,
  };
}

/**
 * Escape string for safe interpolation in TypeScript code
 */
function escapeForTypeScript(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/'/g, "\\'")
    .replace(/`/g, '\\`')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

/**
 * Generate locator code from selector and iframe chain
 * Uses deepLocator for cross-iframe interactions (Stagehand v3 best practice)
 */
function generateLocatorCall(step: StagehandStep): string {
  if (!step.selector) {
    return '';
  }

  const escapedSelector = escapeForTypeScript(step.selector);
  
  if (step.useDeepLocator && step.iframeChain && step.iframeChain.length > 0) {
    // Use deepLocator with >> notation for cross-iframe traversal
    // This is the recommended Stagehand v3 pattern for iframes
    const escapedIframes = step.iframeChain.map(iframe => {
      // If iframe is XPath, prefix with xpath=
      if (iframe.startsWith('//') || iframe.startsWith('/html')) {
        return `xpath=${escapeForTypeScript(iframe)}`;
      }
      return escapeForTypeScript(iframe);
    });
    
    // Add final selector
    const finalSelectorPart = escapedSelector.startsWith('//') || escapedSelector.startsWith('/html')
      ? `xpath=${escapedSelector}`
      : escapedSelector;
    
    const deepLocatorPath = [...escapedIframes, finalSelectorPart].join(' >> ');
    return `page.deepLocator("${deepLocatorPath}")`;
  } else {
    // Use regular locator
    if (escapedSelector.startsWith('//') || escapedSelector.startsWith('/html')) {
      // XPath selector
      return `page.locator("xpath=${escapedSelector}")`;
    } else {
      // CSS selector
      return `page.locator("${escapedSelector}")`;
    }
  }
}

/**
 * Generate action code from step
 * Follows Stagehand v3 best practices for interactions
 */
function generateActionCode(step: StagehandStep, indent: string = '', includeVariables: boolean = false): string {
  const locatorCall = generateLocatorCall(step);
  
  if (!locatorCall) {
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
      if (includeVariables && step.parameters?.variable) {
        // Use variable pattern for sensitive data (Stagehand v3 best practice)
        return `${comment}${indent}await ${locatorCall}.fill(${step.parameters.variable});`;
      }
      const fillValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${comment}${indent}await ${locatorCall}.fill("${fillValue}");`;
    
    case 'type':
      if (includeVariables && step.parameters?.variable) {
        return `${comment}${indent}await ${locatorCall}.type(${step.parameters.variable}, { delay: 100 });`;
      }
      const typeValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${comment}${indent}await ${locatorCall}.type("${typeValue}", { delay: 100 });`;
    
    case 'press':
      const key = escapeForTypeScript(step.parameters?.key || 'Enter');
      return `${comment}${indent}await ${locatorCall}.press("${key}");`;
    
    case 'scroll':
      return `${comment}${indent}await ${locatorCall}.scrollIntoViewIfNeeded();`;
    
    case 'hover':
      return `${comment}${indent}await ${locatorCall}.hover();`;
    
    case 'select':
      if (step.parameters?.options && step.parameters.options.length > 0) {
        const options = step.parameters.options.map(opt => `"${escapeForTypeScript(opt)}"`).join(', ');
        return `${comment}${indent}await ${locatorCall}.selectOption([${options}]);`;
      }
      const selectValue = escapeForTypeScript(step.parameters?.value || '');
      return `${comment}${indent}await ${locatorCall}.selectOption("${selectValue}");`;
    
    default:
      return `${comment}${indent}// Unsupported action: ${step.action}`;
  }
}

/**
 * Generate complete TypeScript code with locators and best practices
 * Includes Stagehand v3 patterns: deepLocator, variables, metrics, fallbacks
 */
export function emitLocatorScript(options: LocatorCodeOptions): string {
  const { 
    url, 
    model, 
    mode, 
    steps, 
    cacheDir,
    variables = {},
    includeMetrics = false,
    includeHistory = false,
    includeFallback = false
  } = options;
  
  const imports = [
    `import { Stagehand } from "@browserbasehq/stagehand";`,
  ];
  
  // Add Zod import if needed for extract mode
  if (mode === 'extract' || steps.some(s => s.action === 'extract')) {
    imports.push(`import { z } from "zod";`);
  }

  const hasVariables = Object.keys(variables).length > 0;
  const cacheDirConfig = cacheDir ? `\n  cacheDir: "${escapeForTypeScript(cacheDir)}",` : '';
  const escapedUrl = escapeForTypeScript(url);
  const escapedModel = escapeForTypeScript(model);
  
  // Variable declarations if present (Stagehand v3 best practice for sensitive data)
  const variableDeclarations = hasVariables 
    ? '\n// Sensitive data variables (best practice: load from env)\n' + 
      Object.entries(variables).map(([key, value]) => 
        `const ${key} = process.env.${key.toUpperCase()} || "${escapeForTypeScript(value)}";`
      ).join('\n') + '\n'
    : '';
  
  const setupCode = `${variableDeclarations}
// Initialize Stagehand with recommended configuration
const stagehand = new Stagehand({
  env: "LOCAL", // or "BROWSERBASE" for cloud browsers
  model: "${escapedModel}", // v3 API format: provider/model${cacheDirConfig}
  verbose: 1, // 0 = minimal, 1 = standard, 2 = debug
  selfHeal: true, // Enable self-healing for resilience
  localBrowserLaunchOptions: {
    headless: false, // Set to true for production
  },
});

await stagehand.init();
const page = stagehand.context.pages()[0];

// Navigate to the target URL
await page.goto("${escapedUrl}", { 
  waitUntil: "domcontentloaded" // Faster than "networkidle" for most cases
});
`;

  // Generate action code for each step
  const actionCodes = steps
    .filter(step => step.action !== 'goto')
    .map(step => generateActionCode(step, '', hasVariables))
    .filter(code => code.trim().length > 0);

  // Add performance optimization comment
  const optimizationComment = steps.length > 3 
    ? `\n// Performance Tip: For ${steps.length} actions, consider using observe() + act() pattern\n// This can be 2-3x faster by caching selectors\n`
    : '';

  // Add metrics tracking if requested (Stagehand v3 feature)
  const metricsCode = includeMetrics ? `
// Track performance metrics (Stagehand v3 feature)
const metrics = await stagehand.metrics;
console.log('Total tokens used:', metrics.totalPromptTokens + metrics.totalCompletionTokens);
console.log('Total inference time:', metrics.totalInferenceTimeMs, 'ms');
` : '';

  // Add history tracking if requested (Stagehand v3 feature)
  const historyCode = includeHistory ? `
// Access operation history (Stagehand v3 feature)
const history = await stagehand.history;
console.log('Operations performed:', history.length);
` : '';

  // Add agent fallback pattern if requested (Stagehand v3 best practice)
  const fallbackPattern = includeFallback ? `
// Agent Fallback Pattern (Stagehand v3 best practice)
// If any action fails, use agent to recover
try {
${actionCodes.map(code => '  ' + code).join('\n\n')}
} catch (error) {
  console.log('Action failed, using agent fallback...');
  
  const agent = stagehand.agent({
    model: "${escapedModel}",
    systemPrompt: "You are a helpful assistant that can recover from automation failures.",
  });
  
  await agent.execute({
    instruction: "Complete the task: ${escapeForTypeScript(steps[0]?.description || 'unknown task')}",
    maxSteps: 10,
  });
}
` : actionCodes.join('\n\n');

  const cleanupCode = `${metricsCode}${historyCode}
// Close the browser and clean up
await stagehand.close();`;

  const fullCode = `${imports.join('\n')}

${setupCode}${optimizationComment}
${fallbackPattern}
${cleanupCode}`;

  return fullCode.trim();
}

/**
 * Generate observe + act optimized version (2-3x faster)
 * Follows Stagehand v3 speed optimization best practices
 */
export function emitOptimizedScript(options: LocatorCodeOptions): string {
  const { url, model, steps } = options;
  
  const actSteps = steps.filter(s => s.action === 'click' || s.action === 'fill' || s.action === 'type');
  
  if (actSteps.length === 0) {
    return emitLocatorScript(options);
  }

  const imports = [`import { Stagehand } from "@browserbasehq/stagehand";`];
  const escapedUrl = escapeForTypeScript(url);
  const escapedModel = escapeForTypeScript(model);

  const setupCode = `
// Optimized pattern: observe + act (2-3x faster)
const stagehand = new Stagehand({
  env: "LOCAL",
  model: "${escapedModel}",
  verbose: 1,
});

await stagehand.init();
const page = stagehand.context.pages()[0];
await page.goto("${escapedUrl}", { waitUntil: "domcontentloaded" });
`;

  const observePrompts = actSteps.map(step => 
    step.description || `${step.action} element`
  ).join(', ');

  const optimizedCode = `
// Single observe call to plan all actions (1 LLM call instead of ${actSteps.length})
const actions = await stagehand.observe("Find elements to: ${escapeForTypeScript(observePrompts)}");

// Execute all actions without LLM inference (2-3x faster!)
for (const action of actions) {
  await stagehand.act(action); // No LLM call - uses cached selector
}
`;

  const cleanupCode = `
await stagehand.close();`;

  return `${imports.join('\n')}${setupCode}${optimizedCode}${cleanupCode}`;
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

/**
 * Generate code with Computer Use Agent (CUA)
 * Follows Stagehand v3 CUA best practices
 */
export function emitAgentScript(options: LocatorCodeOptions): string {
  const { url, model, steps } = options;
  const escapedUrl = escapeForTypeScript(url);
  const escapedModel = escapeForTypeScript(model);
  
  const task = steps[0]?.description || 'Complete the automation task';
  const escapedTask = escapeForTypeScript(task);

  return `import { Stagehand } from "@browserbasehq/stagehand";

// Computer Use Agent configuration (Stagehand v3)
const stagehand = new Stagehand({
  env: "BROWSERBASE", // CUA works best with Browserbase
  model: "${escapedModel}",
  verbose: 2, // Debug mode for agent tasks
  // Configure viewport for optimal CUA performance
  browserbaseSessionCreateParams: {
    browserSettings: {
      viewport: {
        width: 1288,  // Default for optimal CUA performance
        height: 711,  // Don't change unless necessary
      },
    },
  },
});

await stagehand.init();
const page = stagehand.context.pages()[0];

// Navigate first (CUA best practice)
await page.goto("${escapedUrl}");

// Create agent with Computer Use enabled
const agent = stagehand.agent({
  cua: true, // Enable Computer Use Agent
  model: "${escapedModel}",
  systemPrompt: "You are a helpful automation assistant. Be specific and complete tasks fully.",
});

// Execute autonomous multi-step workflow
const result = await agent.execute({
  instruction: "${escapedTask}",
  maxSteps: 20, // Adjust based on task complexity
  highlightCursor: true, // Useful for debugging
});

console.log('Agent result:', result.success);
console.log('Message:', result.message);
console.log('Actions taken:', result.actions.length);

await stagehand.close();`;
}
