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
 * Semantic locator information extracted from selector
 */
interface SemanticLocator {
  type: 'testid' | 'role' | 'label' | 'placeholder' | 'text' | 'title' | 'alt' | null;
  value?: string;
  roleOptions?: { name?: string; exact?: boolean };
}

/**
 * Extract semantic attributes from XPath or CSS selector
 * Prioritizes resilient selectors over brittle DOM structure
 */
function extractSemanticLocator(selector: string): SemanticLocator {
  if (!selector) {
    return { type: null };
  }

  // Check for data-testid (highest priority for stability)
  const testIdMatch = selector.match(/\[@data-testid=['"]([^'"]+)['"]\]|data-testid=['"]([^'"]+)['"]|\[data-testid=['"]([^'"]+)['"]\]/);
  if (testIdMatch) {
    const testId = testIdMatch[1] || testIdMatch[2] || testIdMatch[3];
    return { type: 'testid', value: testId };
  }

  // Check for ARIA role with name (excellent for accessibility)
  const roleMatch = selector.match(/\[@role=['"]([^'"]+)['"]\]|role=['"]([^'"]+)['"]|\[role=['"]([^'"]+)['"]\]/);
  if (roleMatch) {
    const role = roleMatch[1] || roleMatch[2] || roleMatch[3];
    // Try to extract accessible name from aria-label or text content
    const ariaLabelMatch = selector.match(/\[@aria-label=['"]([^'"]+)['"]\]|aria-label=['"]([^'"]+)['"]|\[aria-label=['"]([^'"]+)['"]\]/);
    const exactTextMatch = selector.match(/text\(\)=['"]([^'"]+)['"]\]/);
    const containsTextMatch = selector.match(/contains\(text\(\),\s*['"]([^'"]+)['"]\)/);
    
    const name = (ariaLabelMatch && (ariaLabelMatch[1] || ariaLabelMatch[2] || ariaLabelMatch[3])) ||
                 (exactTextMatch && exactTextMatch[1]) ||
                 (containsTextMatch && containsTextMatch[1]);
    
    // Only use exact: true if the selector uses exact text match (text()=), not contains()
    const isExactMatch = !!exactTextMatch || !!ariaLabelMatch;
    
    return { 
      type: 'role', 
      value: role,
      roleOptions: name ? { name, exact: isExactMatch } : undefined
    };
  }

  // Check for aria-label (good for accessibility)
  const ariaLabelMatch = selector.match(/\[@aria-label=['"]([^'"]+)['"]\]|aria-label=['"]([^'"]+)['"]|\[aria-label=['"]([^'"]+)['"]\]/);
  if (ariaLabelMatch) {
    const label = ariaLabelMatch[1] || ariaLabelMatch[2] || ariaLabelMatch[3];
    return { type: 'label', value: label };
  }

  // Check for placeholder (useful for inputs)
  const placeholderMatch = selector.match(/\[@placeholder=['"]([^'"]+)['"]\]|placeholder=['"]([^'"]+)['"]|\[placeholder=['"]([^'"]+)['"]\]/);
  if (placeholderMatch) {
    const placeholder = placeholderMatch[1] || placeholderMatch[2] || placeholderMatch[3];
    return { type: 'placeholder', value: placeholder };
  }

  // Check for visible text content (more stable than title/alt)
  const textContentMatch = selector.match(/text\(\)=['"]([^'"]+)['"]\]|contains\(text\(\),\s*['"]([^'"]+)['"]\)/);
  if (textContentMatch) {
    const text = textContentMatch[1] || textContentMatch[2];
    return { type: 'text', value: text };
  }

  // Check for title attribute
  const titleMatch = selector.match(/\[@title=['"]([^'"]+)['"]\]|title=['"]([^'"]+)['"]|\[title=['"]([^'"]+)['"]\]/);
  if (titleMatch) {
    const title = titleMatch[1] || titleMatch[2] || titleMatch[3];
    return { type: 'title', value: title };
  }

  // Check for alt text (images)
  const altMatch = selector.match(/\[@alt=['"]([^'"]+)['"]\]|alt=['"]([^'"]+)['"]|\[alt=['"]([^'"]+)['"]\]/);
  if (altMatch) {
    const alt = altMatch[1] || altMatch[2] || altMatch[3];
    return { type: 'alt', value: alt };
  }

  return { type: null };
}

/**
 * Generate resilient Playwright locator using semantic attributes when available
 * Falls back to XPath/CSS if no semantic attributes found
 */
function generateResilientLocator(selector: string): string {
  const semantic = extractSemanticLocator(selector);
  const escapedSelector = escapeForTypeScript(selector);

  switch (semantic.type) {
    case 'testid':
      return `page.getByTestId("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'role':
      if (semantic.roleOptions?.name) {
        return `page.getByRole("${escapeForTypeScript(semantic.value!)}", { name: "${escapeForTypeScript(semantic.roleOptions.name)}" })`;
      }
      return `page.getByRole("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'label':
      return `page.getByLabel("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'placeholder':
      return `page.getByPlaceholder("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'text':
      return `page.getByText("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'title':
      return `page.getByTitle("${escapeForTypeScript(semantic.value!)}")`;
    
    case 'alt':
      return `page.getByAltText("${escapeForTypeScript(semantic.value!)}")`;
    
    default:
      // Fallback to XPath or CSS
      if (escapedSelector.startsWith('//') || escapedSelector.startsWith('/html')) {
        return `page.locator("xpath=${escapedSelector}")`;
      } else {
        return `page.locator("${escapedSelector}")`;
      }
  }
}

/**
 * Generate locator code from selector and iframe chain
 * Uses resilient semantic locators when available, falls back to XPath/CSS
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
    
    // Add final selector - try to use resilient locator first
    const semantic = extractSemanticLocator(step.selector);
    let finalSelectorPart: string;
    
    if (semantic.type) {
      // For semantic selectors in iframes, we need to use a different approach
      // Since deepLocator requires string selectors, we'll use XPath/CSS as fallback
      finalSelectorPart = escapedSelector.startsWith('//') || escapedSelector.startsWith('/html')
        ? `xpath=${escapedSelector}`
        : escapedSelector;
    } else {
      finalSelectorPart = escapedSelector.startsWith('//') || escapedSelector.startsWith('/html')
        ? `xpath=${escapedSelector}`
        : escapedSelector;
    }
    
    const deepLocatorPath = [...escapedIframes, finalSelectorPart].join(' >> ');
    return `page.deepLocator("${deepLocatorPath}")`;
  } else {
    // Use resilient semantic locator when possible (getByRole, getByTestId, etc.)
    return generateResilientLocator(step.selector);
  }
}

/**
 * Generate action code from step with selector strategy annotations
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

  // Detect which selector strategy is being used
  const semantic = step.selector ? extractSemanticLocator(step.selector) : { type: null };
  let selectorStrategyComment = '';
  
  if (semantic.type) {
    const strategyNames = {
      'testid': '✓ Resilient: data-testid',
      'role': '✓ Resilient: ARIA role',
      'label': '✓ Resilient: aria-label',
      'placeholder': '✓ Resilient: placeholder',
      'text': '✓ Semantic: text content',
      'title': '✓ Semantic: title',
      'alt': '✓ Semantic: alt text'
    };
    selectorStrategyComment = `${indent}// ${strategyNames[semantic.type]}\n`;
  } else if (step.selector?.startsWith('//') || step.selector?.startsWith('/html')) {
    selectorStrategyComment = `${indent}// ⚠ Fallback: XPath (may break if DOM changes)\n`;
  } else if (step.selector) {
    selectorStrategyComment = `${indent}// ⚠ Fallback: CSS (may break if DOM changes)\n`;
  }

  const comment = step.description ? `${indent}// ${escapeForTypeScript(step.description)}\n` : '';
  const fullComment = comment + selectorStrategyComment;
  
  switch (step.action) {
    case 'click':
      return `${fullComment}${indent}await ${locatorCall}.click();`;
    
    case 'fill':
      if (includeVariables && step.parameters?.variable) {
        // Use variable pattern for sensitive data (Stagehand v3 best practice)
        return `${fullComment}${indent}await ${locatorCall}.fill(${step.parameters.variable});`;
      }
      const fillValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${fullComment}${indent}await ${locatorCall}.fill("${fillValue}");`;
    
    case 'type':
      if (includeVariables && step.parameters?.variable) {
        return `${fullComment}${indent}await ${locatorCall}.type(${step.parameters.variable}, { delay: 100 });`;
      }
      const typeValue = escapeForTypeScript(step.parameters?.value || step.parameters?.text || '');
      return `${fullComment}${indent}await ${locatorCall}.type("${typeValue}", { delay: 100 });`;
    
    case 'press':
      const key = escapeForTypeScript(step.parameters?.key || 'Enter');
      return `${fullComment}${indent}await ${locatorCall}.press("${key}");`;
    
    case 'scroll':
      return `${fullComment}${indent}await ${locatorCall}.scrollIntoViewIfNeeded();`;
    
    case 'hover':
      return `${fullComment}${indent}await ${locatorCall}.hover();`;
    
    case 'select':
      if (step.parameters?.options && step.parameters.options.length > 0) {
        const options = step.parameters.options.map(opt => `"${escapeForTypeScript(opt)}"`).join(', ');
        return `${fullComment}${indent}await ${locatorCall}.selectOption([${options}]);`;
      }
      const selectValue = escapeForTypeScript(step.parameters?.value || '');
      return `${fullComment}${indent}await ${locatorCall}.selectOption("${selectValue}");`;
    
    default:
      return `${fullComment}${indent}// Unsupported action: ${step.action}`;
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

  // Count selector types for summary
  const selectorStats = steps.reduce((acc, step) => {
    if (!step.selector) return acc;
    const semantic = extractSemanticLocator(step.selector);
    if (semantic.type) {
      acc.resilient++;
    } else {
      acc.fallback++;
    }
    return acc;
  }, { resilient: 0, fallback: 0 });

  const selectorSummary = selectorStats.resilient > 0 || selectorStats.fallback > 0
    ? `/**
 * Generated Code Summary:
 * - ${selectorStats.resilient} resilient selector(s) (getByRole, getByTestId, getByLabel, etc.)
 * - ${selectorStats.fallback} fallback selector(s) (XPath/CSS - may break if DOM changes)
 * 
 * Resilient selectors use Playwright's semantic locators which are:
 * ✓ More stable across UI changes
 * ✓ Aligned with accessibility best practices
 * ✓ Easier to maintain and understand
 * 
 * Priority: data-testid > role > label > placeholder > text > title > alt > XPath/CSS
 */

`
    : '';

  const fullCode = `${imports.join('\n')}

${selectorSummary}${setupCode}${optimizationComment}
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
