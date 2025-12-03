import { chromium, Browser, Page, BrowserContext } from "playwright";

const activeBrowsers = new Map<string, { browser: Browser; context: BrowserContext; page: Page }>();

export interface BrowserActionResult {
  success: boolean;
  result?: string;
  error?: string;
  screenshot?: string;
}

export async function initBrowserForExecution(executionId: string): Promise<void> {
  if (activeBrowsers.has(executionId)) {
    return;
  }
  
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
    ],
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  });
  
  const page = await context.newPage();
  
  activeBrowsers.set(executionId, { browser, context, page });
}

export async function closeBrowserForExecution(executionId: string): Promise<void> {
  const browserData = activeBrowsers.get(executionId);
  if (browserData) {
    try {
      await browserData.context.close();
      await browserData.browser.close();
    } catch (error) {
      console.error(`Error closing browser for execution ${executionId}:`, error);
    }
    activeBrowsers.delete(executionId);
  }
}

export async function getPageForExecution(executionId: string): Promise<Page> {
  const browserData = activeBrowsers.get(executionId);
  if (!browserData) {
    await initBrowserForExecution(executionId);
    return activeBrowsers.get(executionId)!.page;
  }
  return browserData.page;
}

export async function navigateToUrl(executionId: string, url: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    const title = await page.title();
    return {
      success: true,
      result: `Navigated to ${url}. Page title: "${title}"`,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to navigate to ${url}: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function typeText(executionId: string, selector: string, text: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    await page.waitForSelector(selector, { timeout: 10000 });
    await page.fill(selector, text);
    return {
      success: true,
      result: `Typed "${text}" into ${selector}`,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to type text: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function clickElement(executionId: string, selector: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    await page.waitForSelector(selector, { timeout: 10000 });
    await page.click(selector);
    await page.waitForLoadState("domcontentloaded");
    return {
      success: true,
      result: `Clicked on ${selector}`,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to click element: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function pressKey(executionId: string, key: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    await page.keyboard.press(key);
    await page.waitForLoadState("domcontentloaded");
    return {
      success: true,
      result: `Pressed ${key} key`,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to press key: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function extractText(executionId: string, selector?: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    let text: string;
    if (selector) {
      await page.waitForSelector(selector, { timeout: 10000 });
      text = await page.textContent(selector) || "";
    } else {
      text = await page.evaluate(() => document.body.innerText);
    }
    const truncated = text.slice(0, 1000) + (text.length > 1000 ? "..." : "");
    return {
      success: true,
      result: `Extracted text: "${truncated}"`,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to extract text: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function takeScreenshot(executionId: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    const screenshot = await page.screenshot({ type: "png" });
    const base64 = screenshot.toString("base64");
    return {
      success: true,
      result: "Screenshot captured",
      screenshot: base64,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to take screenshot: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function waitForPage(executionId: string): Promise<BrowserActionResult> {
  try {
    const page = await getPageForExecution(executionId);
    await page.waitForLoadState("networkidle", { timeout: 10000 });
    return {
      success: true,
      result: "Page fully loaded",
    };
  } catch (error) {
    return {
      success: true,
      result: "Page load wait completed",
    };
  }
}

export async function executeStep(
  executionId: string,
  stepName: string,
  stepDescription: string,
  tool: string
): Promise<BrowserActionResult> {
  const lowerName = stepName.toLowerCase();
  const lowerDesc = stepDescription.toLowerCase();

  if (lowerName.includes("navigate") || lowerName.includes("open") || lowerName.includes("go to") || lowerName.includes("visit")) {
    const urlMatch = stepDescription.match(/(?:to|at|visit|open)\s+(?:the\s+)?(?:website\s+)?(?:url\s+)?["']?([^\s"']+\.[^\s"',]+)["']?/i) ||
                     stepDescription.match(/(https?:\/\/[^\s]+)/i) ||
                     stepDescription.match(/([a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}(?:\/[^\s]*)?)/i);
    
    if (urlMatch) {
      let url = urlMatch[1];
      if (!url.startsWith("http")) {
        url = "https://" + url;
      }
      return await navigateToUrl(executionId, url);
    }
    
    if (lowerDesc.includes("google")) {
      return await navigateToUrl(executionId, "https://www.google.com");
    }
    
    return {
      success: false,
      error: `Could not determine URL from step: ${stepDescription}`,
    };
  }

  if (lowerName.includes("wait") || lowerName.includes("load")) {
    return await waitForPage(executionId);
  }

  if (lowerName.includes("search") || lowerName.includes("enter") || lowerName.includes("type") || lowerName.includes("input") || lowerName.includes("query")) {
    const searchTermMatch = stepDescription.match(/(?:search|type|enter|input|query)(?:\s+(?:for|term|the|query|text))?\s+['"]?([^'"]+?)['"]?(?:\s+(?:into|in|on)|$)/i) ||
                           stepDescription.match(/['"]([^'"]+)['"]/);
    
    const searchTerm = searchTermMatch ? searchTermMatch[1].trim() : "";
    
    const page = await getPageForExecution(executionId);
    const url = page.url();
    
    if (url.includes("google.com")) {
      const result = await typeText(executionId, 'textarea[name="q"], input[name="q"]', searchTerm || "search query");
      return result;
    }
    
    const commonSelectors = [
      'input[type="search"]',
      'input[name="q"]',
      'input[name="query"]',
      'input[name="search"]',
      'textarea[name="q"]',
      '[role="searchbox"]',
      'input[placeholder*="search" i]',
    ];
    
    for (const selector of commonSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 2000 });
        return await typeText(executionId, selector, searchTerm || "search query");
      } catch {
        continue;
      }
    }
    
    return {
      success: false,
      error: "Could not find search input field",
    };
  }

  if (lowerName.includes("submit") || lowerName.includes("click") || lowerName.includes("press") || lowerName.includes("button")) {
    if (lowerDesc.includes("enter") || lowerDesc.includes("submit") || lowerDesc.includes("search")) {
      return await pressKey(executionId, "Enter");
    }
    
    const page = await getPageForExecution(executionId);
    const buttonSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button:has-text("Search")',
      'button:has-text("Submit")',
      '[role="button"]',
    ];
    
    for (const selector of buttonSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 2000 });
        return await clickElement(executionId, selector);
      } catch {
        continue;
      }
    }
    
    return await pressKey(executionId, "Enter");
  }

  if (lowerName.includes("extract") || lowerName.includes("get") || lowerName.includes("read") || lowerName.includes("scrape")) {
    return await extractText(executionId);
  }

  if (lowerName.includes("screenshot") || lowerName.includes("capture")) {
    return await takeScreenshot(executionId);
  }

  return {
    success: true,
    result: `Step "${stepName}" executed (no specific browser action mapped)`,
  };
}
