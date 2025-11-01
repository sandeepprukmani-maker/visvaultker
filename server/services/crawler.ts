import { chromium, type Browser, type Page, type ElementHandle, type BrowserContext } from "playwright";
import { openAIService } from "./openai";
import type { InsertPage, InsertElement } from "@shared/schema";

export interface CrawlOptions {
  depth?: number;
  waitTime?: number;
  screenshotQuality?: number;
  proxy?: {
    server: string;
    username?: string;
    password?: string;
  };
  cookies?: Array<{
    name: string;
    value: string;
    domain?: string;
    path?: string;
  }>;
  userAgent?: string;
  viewport?: { width: number; height: number };
  javascript?: boolean;
  images?: boolean;
  waitForSelector?: string;
  waitForNetworkIdle?: boolean;
  extractIframes?: boolean;
  extractShadowDOM?: boolean;
}

export interface ElementData {
  tag: string;
  selector: string;
  text?: string;
  attributes: Record<string, string>;
  xpath?: string;
  cssSelector?: string;
  textSelector?: string;
  ariaLabel?: string;
  role?: string;
  isVisible?: boolean;
  isInteractive?: boolean;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  context?: string;
  frame?: string;
  shadowRoot?: boolean;
}

export interface PageData {
  url: string;
  title: string;
  elements: ElementData[];
  screenshot?: string;
  links: string[];
  metadata?: {
    description?: string;
    keywords?: string;
    ogTitle?: string;
    ogDescription?: string;
    ogImage?: string;
  };
  performance?: {
    loadTime: number;
    domContentLoaded: number;
    resourceCount: number;
  };
  iframes?: PageData[];
}

export class CrawlerService {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private currentProxy: string | null = null;

  async initialize(options: CrawlOptions = {}) {
    const newProxy = options.proxy ? JSON.stringify(options.proxy) : null;
    const proxyChanged = this.currentProxy !== newProxy;

    if (proxyChanged || !this.browser) {
      await this.close();
      
      const launchOptions: any = {
        headless: true,
        args: [
          '--disable-blink-features=AutomationControlled',
          '--disable-dev-shm-usage',
          '--no-sandbox',
          '--disable-setuid-sandbox',
        ],
      };

      if (options.proxy) {
        launchOptions.proxy = options.proxy;
      }

      this.browser = await chromium.launch(launchOptions);
      this.currentProxy = newProxy;
    }

    if (this.context) {
      await this.context.close();
    }

    const contextOptions: any = {
      viewport: options.viewport || { width: 1920, height: 1080 },
      userAgent: options.userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      javaScriptEnabled: options.javascript !== false,
      ignoreHTTPSErrors: true,
    };

    this.context = await this.browser.newContext(contextOptions);

    if (options.cookies && options.cookies.length > 0) {
      await this.context.addCookies(options.cookies);
    }

    await this.context.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
      });
    });
  }

  async close() {
    if (this.context) {
      await this.context.close();
      this.context = null;
    }
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async crawlWebsite(
    startUrl: string,
    options: CrawlOptions = {}
  ): Promise<PageData[]> {
    const {
      depth = 3,
      waitTime = 1000,
      screenshotQuality = 80,
    } = options;

    await this.initialize(options);

    const visitedUrls = new Set<string>();
    const pagesData: PageData[] = [];
    const queue: Array<{ url: string; currentDepth: number }> = [
      { url: startUrl, currentDepth: 0 },
    ];

    while (queue.length > 0 && pagesData.length < 100) {
      const { url, currentDepth } = queue.shift()!;

      if (visitedUrls.has(url) || currentDepth > depth) {
        continue;
      }

      visitedUrls.add(url);

      try {
        const pageData = await this.crawlPage(url, {
          waitTime,
          screenshotQuality,
          ...options,
        });
        pagesData.push(pageData);

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

  async crawlPage(
    url: string,
    options: CrawlOptions & { waitTime?: number; screenshotQuality?: number } = {}
  ): Promise<PageData> {
    const { 
      waitTime = 1000, 
      screenshotQuality = 80,
      waitForSelector,
      waitForNetworkIdle = true,
      extractIframes = true,
      extractShadowDOM = true,
    } = options;

    await this.initialize(options);
    const page = await this.context!.newPage();
    const startTime = Date.now();

    try {
      const navigationPromise = page.goto(url, { 
        waitUntil: waitForNetworkIdle ? "networkidle" : "domcontentloaded", 
        timeout: 30000 
      });

      await navigationPromise;

      if (waitForSelector) {
        await page.waitForSelector(waitForSelector, { timeout: 10000 }).catch(() => {});
      }

      await page.waitForTimeout(waitTime);

      const domContentLoaded = Date.now();

      const title = await page.title();

      const metadata = await this.extractMetadata(page);

      const elements = await this.extractElements(page, { 
        extractShadowDOM,
        extractVisible: true,
      });

      const screenshot = await page.screenshot({
        type: "jpeg",
        quality: screenshotQuality,
        fullPage: false,
      });
      const screenshotBase64 = `data:image/jpeg;base64,${screenshot.toString("base64")}`;

      const links = await this.extractLinks(page, url);

      const resourceCount = await page.evaluate(() => {
        return performance.getEntriesByType('resource').length;
      });

      const loadTime = Date.now() - startTime;

      let iframes: PageData[] = [];
      if (extractIframes) {
        iframes = await this.extractIframeContent(page, url, options);
      }

      return {
        url,
        title,
        elements,
        screenshot: screenshotBase64,
        links,
        metadata,
        performance: {
          loadTime,
          domContentLoaded: domContentLoaded - startTime,
          resourceCount,
        },
        iframes: iframes.length > 0 ? iframes : undefined,
      };
    } finally {
      await page.close();
    }
  }

  private async extractMetadata(page: Page): Promise<PageData['metadata']> {
    return await page.evaluate(() => {
      const getMetaContent = (name: string) => {
        const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return meta?.getAttribute('content') || undefined;
      };

      return {
        description: getMetaContent('description'),
        keywords: getMetaContent('keywords'),
        ogTitle: getMetaContent('og:title'),
        ogDescription: getMetaContent('og:description'),
        ogImage: getMetaContent('og:image'),
      };
    });
  }

  private async extractIframeContent(
    page: Page,
    baseUrl: string,
    options: CrawlOptions
  ): Promise<PageData[]> {
    const iframeData: PageData[] = [];

    try {
      const frames = page.frames().filter(f => f.parentFrame() !== null);

      for (const frame of frames.slice(0, 5)) {
        try {
          const frameUrl = frame.url();
          if (!frameUrl || frameUrl === 'about:blank') continue;

          const elements = await this.extractElementsFromFrame(frame);
          const title = await frame.title();

          iframeData.push({
            url: frameUrl,
            title,
            elements,
            links: [],
          });
        } catch (error) {
          console.error('Error extracting iframe:', error);
        }
      }
    } catch (error) {
      console.error('Error processing iframes:', error);
    }

    return iframeData;
  }

  private async extractElementsFromFrame(frame: any): Promise<ElementData[]> {
    const elements: ElementData[] = [];
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
        const els = await frame.$$(selector);
        for (let i = 0; i < Math.min(els.length, 10); i++) {
          const el = els[i];
          const elementData = await this.extractElementData(el, selector, 'iframe');
          if (elementData) {
            elements.push(elementData);
          }
        }
      } catch (error) {
        console.error(`Error in iframe ${selector}:`, error);
      }
    }

    return elements;
  }

  private async extractElements(
    page: Page,
    options: { extractShadowDOM?: boolean; extractVisible?: boolean } = {}
  ): Promise<ElementData[]> {
    const elements: ElementData[] = [];

    const selectors = [
      "button",
      "input",
      "textarea",
      "select",
      "a[href]",
      '[role="button"]',
      '[role="tab"]',
      '[role="menuitem"]',
      '[role="link"]',
      '[onclick]',
      '[type="submit"]',
      '[type="button"]',
      "form",
      '[contenteditable="true"]',
      '[draggable="true"]',
      '[data-testid]',
      '[aria-label]',
    ];

    for (const selector of selectors) {
      try {
        const els = await page.$$(selector);

        for (let i = 0; i < Math.min(els.length, 30); i++) {
          const el = els[i];

          if (options.extractVisible) {
            const isVisible = await el.isVisible().catch(() => false);
            if (!isVisible) continue;
          }

          const elementData = await this.extractElementData(el, selector);
          if (elementData) {
            elements.push(elementData);
          }
        }
      } catch (error) {
        console.error(`Error extracting ${selector}:`, error);
      }
    }

    if (options.extractShadowDOM) {
      const shadowElements = await this.extractShadowDOMElements(page);
      elements.push(...shadowElements);
    }

    return elements;
  }

  private async extractShadowDOMElements(page: Page): Promise<ElementData[]> {
    try {
      return await page.evaluate(() => {
        const elements: any[] = [];
        
        const traverseShadowDOM = (root: Document | ShadowRoot, depth = 0) => {
          if (depth > 5) return;

          const hosts = root.querySelectorAll('*');
          hosts.forEach((host) => {
            if (host.shadowRoot) {
              const shadowElements = host.shadowRoot.querySelectorAll('button, input, a, [role="button"]');
              shadowElements.forEach((el) => {
                const elem = el as HTMLElement;
                elements.push({
                  tag: elem.tagName.toLowerCase(),
                  text: elem.textContent?.trim().substring(0, 100),
                  attributes: (() => {
                    const attrs: Record<string, string> = {};
                    const attrArray = Array.from(elem.attributes);
                    for (const attr of attrArray) {
                      attrs[attr.name] = attr.value;
                    }
                    return attrs;
                  })(),
                  shadowRoot: true,
                });
              });
              
              traverseShadowDOM(host.shadowRoot, depth + 1);
            }
          });
        };

        traverseShadowDOM(document);
        return elements;
      });
    } catch (error) {
      console.error('Error extracting shadow DOM:', error);
      return [];
    }
  }

  private async extractElementData(
    element: ElementHandle,
    baseSelector: string,
    context?: string
  ): Promise<ElementData | null> {
    try {
      const tag = await element.evaluate((el) => (el as Element).tagName.toLowerCase());

      const text = await element.evaluate((el) => {
        const textContent = el.textContent?.trim() || "";
        return textContent.length > 100
          ? textContent.substring(0, 100)
          : textContent;
      });

      const attributes = await element.evaluate((el) => {
        const attrs: Record<string, string> = {};
        const attrArray = Array.from((el as Element).attributes);
        for (const attr of attrArray) {
          attrs[attr.name] = attr.value;
        }
        return attrs;
      });

      const isVisible = await element.isVisible().catch(() => false);
      const isInteractive = await element.isEnabled().catch(() => true);

      const boundingBox = await element.boundingBox();

      const selector = await this.generateSelector(element);

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

      const additionalData = await element.evaluate((el) => {
        const elem = el as HTMLElement;
        return {
          ariaLabel: elem.getAttribute('aria-label') || undefined,
          role: elem.getAttribute('role') || undefined,
        };
      });

      const textSelector = text ? `text="${text}"` : undefined;

      return {
        tag,
        selector,
        cssSelector: selector,
        xpath,
        text,
        textSelector,
        attributes,
        ariaLabel: additionalData.ariaLabel,
        role: additionalData.role,
        isVisible,
        isInteractive,
        boundingBox: boundingBox || undefined,
        context,
      };
    } catch (error) {
      console.error("Error extracting element data:", error);
      return null;
    }
  }

  private async generateSelector(element: ElementHandle): Promise<string> {
    return await element.evaluate((el) => {
      const elem = el as HTMLElement;
      
      if (elem.id) {
        return `#${elem.id}`;
      }

      if (elem.getAttribute("data-testid")) {
        return `[data-testid="${elem.getAttribute("data-testid")}"]`;
      }

      if (elem.getAttribute("name")) {
        return `[name="${elem.getAttribute("name")}"]`;
      }

      if (elem.getAttribute("aria-label")) {
        return `[aria-label="${elem.getAttribute("aria-label")}"]`;
      }

      if (elem.getAttribute("role")) {
        return `[role="${elem.getAttribute("role")}"]`;
      }

      if (elem.className && typeof elem.className === "string") {
        const classes = elem.className.split(" ").filter((c: string) => c && !c.match(/^(hover|focus|active|disabled)/));
        if (classes.length > 0 && classes.length < 5) {
          return `${elem.tagName.toLowerCase()}.${classes.join(".")}`;
        }
      }

      const parent = elem.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children);
        const index = siblings.indexOf(elem) + 1;
        return `${elem.tagName.toLowerCase()}:nth-child(${index})`;
      }

      return elem.tagName.toLowerCase();
    });
  }

  private async extractLinks(page: Page, baseUrl: string): Promise<string[]> {
    const links = await page.$$eval("a[href]", (anchors) =>
      anchors.map((a) => (a as HTMLAnchorElement).href)
    );

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
        return `${url.origin}${url.pathname}`;
      })
      .filter((link, index, self) => self.indexOf(link) === index)
      .slice(0, 50);
  }

  private isSameDomain(url1: string, url2: string): boolean {
    try {
      const domain1 = new URL(url1).hostname;
      const domain2 = new URL(url2).hostname;
      return domain1 === domain2;
    } catch {
      return false;
    }
  }

  async getCookies(): Promise<any[]> {
    if (this.context) {
      return await this.context.cookies();
    }
    return [];
  }

  async setCookies(cookies: any[]): Promise<void> {
    if (this.context) {
      await this.context.addCookies(cookies);
    }
  }

  async getLocalStorage(url: string): Promise<Record<string, string>> {
    if (!this.context) return {};
    
    const page = await this.context.newPage();
    try {
      await page.goto(url);
      const storage = await page.evaluate(() => {
        const items: Record<string, string> = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key) {
            items[key] = localStorage.getItem(key) || '';
          }
        }
        return items;
      });
      return storage;
    } finally {
      await page.close();
    }
  }
}

export const crawlerService = new CrawlerService();
