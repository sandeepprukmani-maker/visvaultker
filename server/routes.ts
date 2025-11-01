import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { crawlerService } from "./services/crawler";
import { openAIService } from "./services/openai";
import { automationService } from "./services/automation";
import { insertCrawlSessionSchema, insertAutomationSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Crawl endpoints
  app.post("/api/crawl", async (req, res) => {
    try {
      const data = insertCrawlSessionSchema.parse(req.body);
      
      // Create crawl session
      const session = await storage.createCrawlSession(data);
      
      // Start crawling in background
      (async () => {
        try {
          await storage.updateCrawlSession(session.id, { status: "running" });
          
          const pagesData = await crawlerService.crawlWebsite(data.url, {
            depth: data.depth,
          });

          // Save all pages and elements
          for (const pageData of pagesData) {
            // Analyze page with AI
            const analysis = await openAIService.analyzePage({
              url: pageData.url,
              title: pageData.title,
              elements: pageData.elements.slice(0, 30),
            });

            // Save page
            const page = await storage.createPage({
              crawlSessionId: session.id,
              url: pageData.url,
              title: pageData.title || analysis.pageType,
              elementCount: pageData.elements.length,
              screenshot: pageData.screenshot,
              templateHash: null,
              templateGroup: null,
            });

            // Save elements
            for (const elementData of pageData.elements) {
              // Generate embedding for important elements
              let embedding: string | undefined;
              if (elementData.text && elementData.text.length > 3) {
                try {
                  const embeddingVector = await openAIService.generateEmbedding(
                    `${elementData.tag} ${elementData.text} ${elementData.selector}`
                  );
                  embedding = JSON.stringify(embeddingVector);
                } catch (error) {
                  console.error("Error generating embedding:", error);
                }
              }

              await storage.createElement({
                pageId: page.id,
                tag: elementData.tag,
                selector: elementData.selector,
                text: elementData.text,
                attributes: elementData.attributes,
                xpath: elementData.xpath,
                confidence: 100,
                embedding,
              });
            }
          }

          await storage.updateCrawlSession(session.id, {
            status: "completed",
            pagesFound: pagesData.length,
            elementsFound: pagesData.reduce((sum, p) => sum + p.elements.length, 0),
            completedAt: new Date(),
          });
        } catch (error) {
          console.error("Crawl error:", error);
          await storage.updateCrawlSession(session.id, {
            status: "failed",
            completedAt: new Date(),
          });
        }
      })();

      res.json(session);
    } catch (error) {
      res.status(400).json({ error: String(error) });
    }
  });

  app.get("/api/crawl", async (_req, res) => {
    const sessions = await storage.getAllCrawlSessions();
    res.json(sessions);
  });

  app.get("/api/crawl/:id", async (req, res) => {
    const session = await storage.getCrawlSession(req.params.id);
    if (!session) {
      return res.status(404).json({ error: "Session not found" });
    }
    res.json(session);
  });

  // Pages endpoints
  app.get("/api/pages", async (_req, res) => {
    const pages = await storage.getAllPages();
    res.json(pages);
  });

  app.get("/api/pages/:id", async (req, res) => {
    const page = await storage.getPage(req.params.id);
    if (!page) {
      return res.status(404).json({ error: "Page not found" });
    }
    res.json(page);
  });

  app.get("/api/pages/:id/elements", async (req, res) => {
    const elements = await storage.getElementsByPage(req.params.id);
    res.json(elements);
  });

  // Elements endpoints
  app.get("/api/elements", async (req, res) => {
    const query = req.query.q as string;
    if (query) {
      const elements = await storage.searchElements(query);
      res.json(elements);
    } else {
      res.json([]);
    }
  });

  // Automation endpoints
  app.post("/api/automations", async (req, res) => {
    try {
      const data = insertAutomationSchema.parse(req.body);
      
      // Create automation record
      const automation = await storage.createAutomation(data);

      // Generate automation plan in background and execute
      (async () => {
        try {
          await storage.updateAutomation(automation.id, { status: "running" });
          
          // Get all crawled pages for context
          const pages = await storage.getAllPages();
          const pagesWithElements = await Promise.all(
            pages.slice(0, 10).map(async (page) => {
              const elements = await storage.getElementsByPage(page.id);
              return {
                url: page.url,
                title: page.title,
                pageType: page.title, // In MVP, using title as pageType
                elements: elements.slice(0, 20).map((el) => ({
                  tag: el.tag,
                  text: el.text || undefined,
                  selector: el.selector,
                })),
              };
            })
          );

          // Generate automation plan
          const plan = await openAIService.generateAutomationPlan(
            data.command,
            pagesWithElements
          );

          await storage.updateAutomation(automation.id, {
            plan: plan as any,
          });

          // Execute automation
          const baseUrl = pages.length > 0 ? new URL(pages[0].url).origin : undefined;
          const result = await automationService.executeAutomation(
            automation.id,
            plan.steps,
            { baseUrl }
          );

          // Save logs
          for (const log of result.logs) {
            await storage.createAutomationLog(log);
          }

          // Update automation
          await storage.updateAutomation(automation.id, {
            status: result.success ? "success" : "error",
            result: result as any,
            duration: result.duration,
            actionCount: plan.steps.length,
            completedAt: new Date(),
          });
        } catch (error) {
          console.error("Automation error:", error);
          await storage.updateAutomation(automation.id, {
            status: "error",
            result: { error: String(error) } as any,
            completedAt: new Date(),
          });
        }
      })();

      res.json(automation);
    } catch (error) {
      res.status(400).json({ error: String(error) });
    }
  });

  app.get("/api/automations", async (_req, res) => {
    const automations = await storage.getAllAutomations();
    res.json(automations);
  });

  app.get("/api/automations/:id", async (req, res) => {
    const automation = await storage.getAutomation(req.params.id);
    if (!automation) {
      return res.status(404).json({ error: "Automation not found" });
    }
    res.json(automation);
  });

  app.get("/api/automations/:id/logs", async (req, res) => {
    const logs = await storage.getAutomationLogs(req.params.id);
    res.json(logs);
  });

  // Dashboard stats endpoint
  app.get("/api/stats", async (_req, res) => {
    const pages = await storage.getAllPages();
    const automations = await storage.getAllAutomations();
    const sessions = await storage.getAllCrawlSessions();
    
    const successfulAutomations = automations.filter(a => a.status === "success").length;
    const totalAutomations = automations.filter(a => a.status !== "queued").length;
    const successRate = totalAutomations > 0 
      ? ((successfulAutomations / totalAutomations) * 100).toFixed(1)
      : "0.0";

    const totalElements = pages.reduce((sum, p) => sum + p.elementCount, 0);

    res.json({
      pagesCrawled: pages.length,
      elementsIndexed: totalElements,
      automationsRun: automations.length,
      successRate: `${successRate}%`,
      crawlSessions: sessions.length,
    });
  });

  // Settings endpoints
  app.get("/api/settings", async (_req, res) => {
    const settings = await storage.getSettings();
    res.json(settings);
  });

  app.post("/api/settings", async (req, res) => {
    try {
      const settings = await storage.updateSettings(req.body);
      res.json(settings);
    } catch (error) {
      res.status(400).json({ error: String(error) });
    }
  });

  // Visual Intelligence endpoints
  app.post("/api/visual/analyze-screenshot", async (req, res) => {
    try {
      const { screenshot, query } = req.body;
      if (!screenshot) {
        return res.status(400).json({ error: "Screenshot required" });
      }
      const analysis = await openAIService.analyzeScreenshot(screenshot, query);
      res.json(analysis);
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/visual/compare-screenshots", async (req, res) => {
    try {
      const { screenshot1, screenshot2 } = req.body;
      if (!screenshot1 || !screenshot2) {
        return res.status(400).json({ error: "Both screenshots required" });
      }
      const comparison = await openAIService.compareScreenshots(screenshot1, screenshot2);
      res.json(comparison);
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/visual/find-element", async (req, res) => {
    try {
      const { screenshot, description } = req.body;
      if (!screenshot || !description) {
        return res.status(400).json({ error: "Screenshot and description required" });
      }
      const location = await openAIService.findElementByVisual(screenshot, description);
      res.json({ location });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/visual/generate-selectors", async (req, res) => {
    try {
      const { elementDescription, pageUrl } = req.body;
      if (!elementDescription || !pageUrl) {
        return res.status(400).json({ error: "Element description and page URL required" });
      }
      
      const page = await storage.getAllPages();
      const targetPage = page.find(p => p.url === pageUrl);
      if (!targetPage) {
        return res.status(404).json({ error: "Page not found" });
      }
      
      const elements = await storage.getElementsByPage(targetPage.id);
      const selectors = await openAIService.generateSmartSelectors(elementDescription, {
        url: pageUrl,
        elements: elements.map(el => ({
          tag: el.tag,
          text: el.text || undefined,
          attributes: el.attributes as Record<string, string>,
        })),
      });
      
      res.json(selectors);
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  // Action Recorder endpoints
  app.post("/api/recorder/start", async (req, res) => {
    try {
      const { url, duration } = req.body;
      if (!url) {
        return res.status(400).json({ error: "URL required" });
      }
      
      const actions = await automationService.recordActions(url, duration || 60000);
      res.json({ actions });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/recorder/export", async (req, res) => {
    try {
      const { actions, name, description } = req.body;
      if (!actions || !Array.isArray(actions)) {
        return res.status(400).json({ error: "Actions array required" });
      }
      
      const template = {
        name: name || `Recording ${new Date().toISOString()}`,
        description: description || '',
        steps: actions,
        createdAt: new Date().toISOString(),
      };
      
      res.json({ template });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  // Data Extraction endpoints
  app.post("/api/extract/data", async (req, res) => {
    try {
      const { url, selector, type } = req.body;
      if (!url || !selector) {
        return res.status(400).json({ error: "URL and selector required" });
      }

      await automationService.initialize();
      
      const step = {
        action: type === 'table' ? 'extractTable' : 'extract',
        selector,
        value: 'extracted_data',
        description: `Extract data from ${selector}`,
      };

      const result = await automationService.executeAutomation(
        'extraction-' + Date.now(),
        [
          { action: 'navigate', value: url, description: `Navigate to ${url}` },
          step,
        ],
        { baseUrl: url }
      );

      res.json({
        success: result.success,
        data: result.data,
        error: result.error,
      });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/extract/export", async (req, res) => {
    try {
      const { data, format } = req.body;
      if (!data) {
        return res.status(400).json({ error: "Data required" });
      }

      if (format === 'csv') {
        const headers = Object.keys(data[0] || {});
        const csvRows = [
          headers.join(','),
          ...data.map((row: any) => 
            headers.map(h => JSON.stringify(row[h] || '')).join(',')
          ),
        ];
        
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', 'attachment; filename=export.csv');
        res.send(csvRows.join('\n'));
      } else {
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', 'attachment; filename=export.json');
        res.json(data);
      }
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  // Session Management endpoints
  app.get("/api/session/cookies", async (req, res) => {
    try {
      const cookies = await crawlerService.getCookies();
      res.json({ cookies });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.post("/api/session/cookies", async (req, res) => {
    try {
      const { cookies } = req.body;
      if (!cookies || !Array.isArray(cookies)) {
        return res.status(400).json({ error: "Cookies array required" });
      }
      
      await crawlerService.setCookies(cookies);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  app.get("/api/session/storage/:url", async (req, res) => {
    try {
      const url = decodeURIComponent(req.params.url);
      const localStorage = await crawlerService.getLocalStorage(url);
      res.json({ localStorage });
    } catch (error) {
      res.status(500).json({ error: String(error) });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
