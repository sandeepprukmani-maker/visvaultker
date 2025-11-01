import { chromium, type Browser, type Page, type ElementHandle } from "playwright";
import { openAIService } from "./openai";
import type { InsertPage, InsertElement } from "@shared/schema";

export interface CrawlOptions {
  depth?: number;
  waitTime?: number;
  screenshotQuality?: number;
}

export interface ElementData {
  tag: string;
  selector: string;
  text?: string;
  attributes: Record<string, string>;
  xpath?: string;
}

export interface PageData {
  url: string;
  title: string;
  elements: ElementData[];
  screenshot?: string;
  links: string[];
}

export class CrawlerService {
  private browser: Browser | null = null;

  async initialize() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
      });
    }
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Crawl a website starting from the given URL
   */
  async crawlWebsite(
    startUrl: string,
    options: CrawlOptions = {}
  ): Promise<PageData[]> {
    const {
      depth = 3,
      waitTime = 1000,
      screenshotQuality = 80,
    } = options;

    await this.initialize();

    const visitedUrls = new Set<string>();
    const pagesData: PageData[] = [];
    const queue: Array<{ url: string; currentDepth: number }> = [
      { url: startUrl, currentDepth: 0 },
    ];

    while (queue.length > 0 && pagesData.length < 50) {
      // Limit to 50 pages for MVP
      const { url, currentDepth } = queue.shift()!;

      if (visitedUrls.has(url) || currentDepth > depth) {
        continue;
      }

      visitedUrls.add(url);

      try {
        const pageData = await this.crawlPage(url, {
          waitTime,
          screenshotQuality,
        });
        pagesData.push(pageData);

        // Add new links to queue if we haven't reached max depth
        if (currentDepth < depth) {
          pageData.links.forEach((link) => {
            if (!visitedUrls.has(link) && this.isSameDomain(startUrl, link)) {
              queue.push({ url: link, currentDepth: currentDepth + 1 });
            }
          });
        }
      } catch (error) {
        console.error(`Error crawling ${url}:`, error);
      }
    }

    return pagesData;
  }

  /**
   * Crawl a single page and extract all relevant information
   */
  async crawlPage(
    url: string,
    options: { waitTime?: number; screenshotQuality?: number } = {}
  ): Promise<PageData> {
    const { waitTime = 1000, screenshotQuality = 80 } = options;

    await this.initialize();
    const page = await this.browser!.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
      await page.waitForTimeout(waitTime);

      const title = await page.title();

      // Extract all interactive elements
      const elements = await this.extractElements(page);

      // Capture screenshot
      const screenshot = await page.screenshot({
        type: "jpeg",
        quality: screenshotQuality,
        fullPage: false,
      });
      const screenshotBase64 = `data:image/jpeg;base64,${screenshot.toString("base64")}`;

      // Extract all links
      const links = await this.extractLinks(page, url);

      return {
        url,
        title,
        elements,
        screenshot: screenshotBase64,
        links,
      };
    } finally {
      await page.close();
    }
  }

  /**
   * Extract interactive elements from a page
   */
  private async extractElements(page: Page): Promise<ElementData[]> {
    const elements: ElementData[] = [];

    // Define selectors for interactive elements
    const selectors = [
      "button",
      "input",
      "textarea",
      "select",
      "a[href]",
      '[role="button"]',
      '[onclick]',
      '[type="submit"]',
      "form",
    ];

    for (const selector of selectors) {
      try {
        const els = await page.$$(selector);

        for (let i = 0; i < Math.min(els.length, 20); i++) {
          // Limit per selector type
          const el = els[i];
          const elementData = await this.extractElementData(el, selector);
          if (elementData) {
            elements.push(elementData);
          }
        }
      } catch (error) {
        console.error(`Error extracting ${selector}:`, error);
      }
    }

    return elements;
  }

  /**
   * Extract data from a single element
   */
  private async extractElementData(
    element: ElementHandle,
    baseSelector: string
  ): Promise<ElementData | null> {
    try {
      const tag = await element.evaluate((el) => el.tagName.toLowerCase());

      // Get text content
      const text = await element.evaluate((el) => {
        const textContent = el.textContent?.trim() || "";
        return textContent.length > 100
          ? textContent.substring(0, 100)
          : textContent;
      });

      // Get attributes
      const attributes = await element.evaluate((el) => {
        const attrs: Record<string, string> = {};
        for (const attr of el.attributes) {
          attrs[attr.name] = attr.value;
        }
        return attrs;
      });

      // Generate a unique selector
      const selector = await this.generateSelector(element);

      // Generate XPath
      const xpath = await element.evaluate((el) => {
        const elem = el as Element;
        const getXPath = (element: Element): string => {
          if ((element as HTMLElement).id) {
            return `//*[@id="${(element as HTMLElement).id}"]`;
          }
          if (element === document.body) {
            return "/html/body";
          }
          let ix = 0;
          const siblings = element.parentNode?.children || [];
          for (let i = 0; i < siblings.length; i++) {
            const sibling = siblings[i];
            if (sibling === element) {
              return `${getXPath(element.parentElement!)}/${element.tagName.toLowerCase()}[${ix + 1}]`;
            }
            if (sibling.tagName === element.tagName) {
              ix++;
            }
          }
          return "";
        };
        return getXPath(elem);
      });

      return {
        tag,
        selector,
        text,
        attributes,
        xpath,
      };
    } catch (error) {
      console.error("Error extracting element data:", error);
      return null;
    }
  }

  /**
   * Generate a unique CSS selector for an element
   */
  private async generateSelector(element: ElementHandle): Promise<string> {
    return await element.evaluate((el) => {
      const elem = el as HTMLElement;
      
      // Prefer ID
      if (elem.id) {
        return `#${elem.id}`;
      }

      // Try name attribute
      if (elem.getAttribute("name")) {
        return `[name="${elem.getAttribute("name")}"]`;
      }

      // Try data-testid
      if (elem.getAttribute("data-testid")) {
        return `[data-testid="${elem.getAttribute("data-testid")}"]`;
      }

      // Try aria-label
      if (elem.getAttribute("aria-label")) {
        return `[aria-label="${elem.getAttribute("aria-label")}"]`;
      }

      // Try class combination
      if (elem.className && typeof elem.className === "string") {
        const classes = elem.className.split(" ").filter((c: string) => c);
        if (classes.length > 0 && classes.length < 4) {
          return `.${classes.join(".")}`;
        }
      }

      // Fall back to tag with position
      const parent = elem.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children);
        const index = siblings.indexOf(elem) + 1;
        return `${elem.tagName.toLowerCase()}:nth-child(${index})`;
      }

      return elem.tagName.toLowerCase();
    });
  }

  /**
   * Extract all links from a page
   */
  private async extractLinks(page: Page, baseUrl: string): Promise<string[]> {
    const links = await page.$$eval("a[href]", (anchors) =>
      anchors.map((a) => (a as HTMLAnchorElement).href)
    );

    // Filter and normalize links
    const base = new URL(baseUrl);
    return links
      .filter((link) => {
        try {
          const url = new URL(link);
          return url.protocol === "http:" || url.protocol === "https:";
        } catch {
          return false;
        }
      })
      .map((link) => {
        const url = new URL(link);
        // Remove hash and query params for deduplication
        return `${url.origin}${url.pathname}`;
      })
      .filter((link, index, self) => self.indexOf(link) === index) // Unique only
      .slice(0, 20); // Limit to 20 links
  }

  /**
   * Check if two URLs are from the same domain
   */
  private isSameDomain(url1: string, url2: string): boolean {
    try {
      const domain1 = new URL(url1).hostname;
      const domain2 = new URL(url2).hostname;
      return domain1 === domain2;
    } catch {
      return false;
    }
  }
}

export const crawlerService = new CrawlerService();
