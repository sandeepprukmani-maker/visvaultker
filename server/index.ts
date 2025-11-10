import "dotenv/config";
import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import getPort from "get-port";

const app = express();

// Extend IncomingMessage to store rawBody
declare module "http" {
  interface IncomingMessage {
    rawBody: unknown;
  }
}

// Parse JSON & URL-encoded requests, keeping raw body for signature validation
app.use(express.json({
  verify: (req, _res, buf) => {
    req.rawBody = buf;
  }
}));
app.use(express.urlencoded({ extended: false }));

// Custom logger for /api routes
app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }
      if (logLine.length > 120) {
        logLine = logLine.slice(0, 119) + "…";
      }
      log(logLine);
    }
  });

  next();
});

(async () => {
  const server = await registerRoutes(app);

  // Central error handler (safe — no process crash)
  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";
    res.status(status).json({ message });
    console.error("Unhandled error:", err);
  });

  // Setup Vite or static serving depending on environment
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // Determine base port from .env or fallback to 5000
  const basePort = parseInt(process.env.PORT || "5000", 10);

  // Automatically find an available port starting from basePort
  const availablePort = await getPort({ port: basePort });
  const host = "0.0.0.0";

  server.listen(availablePort, host, () => {
    log(`✅ Serving on port ${availablePort}`);
    if (availablePort !== basePort) {
      log(`⚠️ Port ${basePort} was busy, switched to ${availablePort}`);
    }
  });
})();
