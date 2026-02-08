import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { 
  tokenResponseSchema, layoutResponseSchema, quoteResponseSchema 
} from "@shared/schema";
import swaggerJsdoc from "swagger-jsdoc";
import swaggerUi from "swagger-ui-express";
import { Agent as UndiciAgent } from "undici";
import tls from "tls";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  // ---- UWM routing (direct vs SSH tunnel) ----
  const UWM_BASE_URL = "https://stg.api.uwm.com";
  const USE_UWM_TUNNEL = process.env.USE_UWM_TUNNEL === "true";
  const TUNNEL_HOST = process.env.UWM_TUNNEL_HOST || "127.0.0.1";
  const TUNNEL_PORT = Number(process.env.UWM_TUNNEL_LOCAL_PORT || "9000");

  // When tunnel is enabled, connect to local forward, but keep TLS SNI as stg.api.uwm.com
  const uwmTunnelDispatcher = new UndiciAgent({
    connect: {
      // @ts-ignore: host is the correct property for undici connection options
      host: TUNNEL_HOST,   // <-- connects to local SSH forward
      port: TUNNEL_PORT,       // <-- 9000
      servername: "stg.api.uwm.com", // <-- SNI/TLS for Cloudflare
    },
  });

  function uwmFetch(path: string, init: any = {}) {
    const url = path.startsWith("http") ? path : `${UWM_BASE_URL}${path}`;
    return fetch(url, {
      ...init,
      ...(USE_UWM_TUNNEL ? { dispatcher: uwmTunnelDispatcher } : {}),
    });
  }

  const swaggerOptions = {
    definition: {
      openapi: "3.0.0",
      info: {
        title: "UWM Public API: Instant Price Quote",
        description: "API documentation for UWM Instant Price Quote based on the Onboarding Guide.",
        version: "3.0",
      },
      components: {
        securitySchemes: {
          bearerAuth: {
            type: "http",
            scheme: "bearer",
            bearerFormat: "JWT",
          },
        },
      },
      security: [
        {
          bearerAuth: [],
        },
      ],
    },
    apis: ["./server/routes.ts"],
  };

  const swaggerSpec = swaggerJsdoc(swaggerOptions);
  app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

  /**
   * @openapi
   * /adfs/oauth2/token:
   *   post:
   *     tags: [Authentication]
   *     summary: Create a bearer token and refresh token.
   *     security: []
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required: [grant_type, client_id, client_secret]
   *             properties:
   *               grant_type:
   *                 type: string
   *                 enum: [password, refresh_token]
   *                 description: Must be 'password' or 'refresh_token'
   *               username:
   *                 type: string
   *                 description: Required if grant_type is 'password'
   *               password:
   *                 type: string
   *                 description: Required if grant_type is 'password'
   *               client_id:
   *                 type: string
   *               client_secret:
   *                 type: string
   *               scope:
   *                 type: string
   *                 description: Required if grant_type is 'password'
   *     responses:
   *       200:
   *         description: Token response
   */
  app.post(api.auth.token.path, async (req, res) => {
    try {
      const input = api.auth.token.input.parse(req.body);

      // Proxy to UWM ADFS via tunnel
      const params = new URLSearchParams();
      params.append("grant_type", input.grant_type);
      params.append("client_id", input.client_id);
      params.append("client_secret", input.client_secret);
      if (input.username) params.append("username", input.username);
      if (input.password) params.append("password", input.password);
      if (input.scope) params.append("scope", input.scope); // Use scope from request if provided
      if (!input.scope && input.grant_type === "password") params.append("scope", "openid");
      if (input.refresh_token) params.append("refresh_token", input.refresh_token);

      const uwmRes = await uwmFetch("/adfs/oauth2/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params.toString(),
      });

      const text = await uwmRes.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("Non-JSON response from UWM auth:", text);
        return res.status(502).json({ error: "bad_gateway", error_description: "UWM returned non-JSON response" });
      }

      if (!uwmRes.ok) {
        return res.status(uwmRes.status).json(data);
      }
      
      res.json(data);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ error: "invalid_request", error_description: err.errors[0].message });
      }
      console.error("Auth proxy error:", err);
      res.status(500).json({ error: "server_error" });
    }
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/mortgagepricinglayout:
   *   post:
   *     tags: [Mortgage]
   *     summary: Retrieves a partial list of components for non-HELOC pricing scenario.
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               PreScenarioId:
   *                 type: string
   *               ObfuscatedScenarioId:
   *                 type: string
   *     responses:
   *       200:
   *         description: Layout response
   */
  app.post(api.layouts.mortgage.path, async (req, res) => {
    // Verify header (simple check)
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
       return res.status(401).json({ message: "Unauthorized" });
    }

    try {
      const uwmRes = await uwmFetch("/instantpricequote/v1/mortgagepricinglayout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader,
        },
        body: JSON.stringify(req.body),
      });

      const data = await uwmRes.json();
      if (!uwmRes.ok) {
        return res.status(uwmRes.status).json(data);
      }
      res.json(data);
    } catch (err) {
      console.error("Mortgage layout proxy error:", err);
      res.status(500).json({ message: "Internal Server Error" });
    }
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/heloclayout:
   *   post:
   *     tags: [HELOC]
   *     summary: Retrieves a partial list of components for HELOC pricing scenario.
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             properties:
   *               PreScenarioId:
   *                 type: string
   *               ObfuscatedScenarioId:
   *                 type: string
   *     responses:
   *       200:
   *         description: Layout response
   */
  app.post(api.layouts.heloc.path, async (req, res) => {
     const authHeader = req.headers.authorization;
     if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }

     try {
       const uwmRes = await uwmFetch("/instantpricequote/v1/heloclayout", {
         method: "POST",
         headers: {
           "Content-Type": "application/json",
           "Authorization": authHeader,
         },
         body: JSON.stringify(req.body),
       });

       const data = await uwmRes.json();
       if (!uwmRes.ok) {
         return res.status(uwmRes.status).json(data);
       }
       res.json(data);
     } catch (err) {
       console.error("HELOC layout proxy error:", err);
       res.status(500).json({ message: "Internal Server Error" });
     }
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/pricequote:
   *   post:
   *     tags: [Mortgage]
   *     summary: Creates a pricing scenario for a non-HELOC loan product.
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required: [loanAmount, loanTypeIds, salesPrice, appraisedValue, purposeTypeId, propertyTypeId, occupancyTypeId, propertyZipCode, creditScore, monthlyIncome, borrowerName]
   *             properties:
   *               brokerAlias:
   *                 type: string
   *               loanOfficer:
   *                 type: string
   *               loanAmount:
   *                 type: number
   *               loanTypeIds:
   *                 type: array
   *                 items:
   *                   type: string
   *               salesPrice:
   *                 type: number
   *               appraisedValue:
   *                 type: number
   *               purposeTypeId:
   *                 type: string
   *               firstTimeHomeBuyer:
   *                 type: boolean
   *               propertyTypeId:
   *                 type: string
   *               occupancyTypeId:
   *                 type: string
   *               propertyZipCode:
   *                 type: string
   *               creditScore:
   *                 type: integer
   *               monthlyIncome:
   *                 type: number
   *               borrowerName:
   *                 type: string
   *               numberOfUnits:
   *                 type: integer
   *               attachmentTypeId:
   *                 type: string
   *               prepaymentPenaltyId:
   *                 type: string
   *               numberOfFinancedProperties:
   *                 type: integer
   *               leaseTypeId:
   *                 type: string
   *               isFirstTimeInvestor:
   *                 type: boolean
   *               debtServiceCreditRatio:
   *                 type: number
   *               refinancePurposeID:
   *                 type: string
   *               mortgageInsuranceType:
   *                 type: integer
   *               controlYourPrice:
   *                 type: integer
   *                 minimum: 0
   *                 maximum: 40
   *     responses:
   *       200:
   *         description: Quote response
   */
  app.post(api.quotes.mortgage.path, async (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return res.status(401).json({ message: "Unauthorized" });
    }

    try {
      const input = api.quotes.mortgage.input.parse(req.body);

      // Proxy to UWM via tunnel
      const uwmRes = await uwmFetch("/instantpricequote/v1/pricequote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader,
        },
        body: JSON.stringify(req.body),
      });

      const mockResponse = await uwmRes.json();
      if (!uwmRes.ok) {
        return res.status(uwmRes.status).json(mockResponse);
      }

      // Persist this scenario
      await storage.createScenario({
        loanAmount: input.loanAmount,
        borrowerName: input.borrowerName,
        creditScore: input.creditScore,
        propertyZipCode: input.propertyZipCode,
        rawRequest: input,
        rawResponse: mockResponse,
      });

      res.json(mockResponse);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message, field: err.errors[0].path.join('.') });
      }
      console.error("Quote proxy error:", err);
      res.status(500).json({ message: "Internal Server Error" });
    }
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/helocquote:
   *   post:
   *     tags: [HELOC]
   *     summary: Creates a pricing scenario for a HELOC loan product.
   *     requestBody:
   *       required: true
   *       content:
   *         application/json:
   *           schema:
   *             type: object
   *             required: [loanAmount, propertyZipCode, creditScore, monthlyIncome, borrowerName]
   *             properties:
   *               brokerAlias:
   *                 type: string
   *               loanOfficer:
   *                 type: string
   *               loanAmount:
   *                 type: number
   *               propertyZipCode:
   *                 type: string
   *               creditScore:
   *                 type: integer
   *               monthlyIncome:
   *                 type: number
   *               borrowerName:
   *                 type: string
   *               additionalData:
   *                 type: object
   *                 additionalProperties: true
   *     responses:
   *       200:
   *         description: Quote response
   */
  app.post(api.quotes.heloc.path, async (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return res.status(401).json({ message: "Unauthorized" });
    }

    try {
      const input = api.quotes.heloc.input.parse(req.body);

      // Proxy to UWM via tunnel
      const uwmRes = await uwmFetch("/instantpricequote/v1/helocquote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": authHeader,
        },
        body: JSON.stringify(req.body),
      });

      const mockResponse = await uwmRes.json();
      if (!uwmRes.ok) {
        return res.status(uwmRes.status).json(mockResponse);
      }

      // Persist this scenario
      await storage.createScenario({
        loanAmount: input.loanAmount,
        borrowerName: input.borrowerName,
        creditScore: input.creditScore,
        propertyZipCode: input.propertyZipCode,
        rawRequest: input,
        rawResponse: mockResponse,
      });

      res.json(mockResponse);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message, field: err.errors[0].path.join('.') });
      }
      console.error("HELOC quote proxy error:", err);
      res.status(500).json({ message: "Internal Server Error" });
    }
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/scenarios:
   *   get:
   *     tags: [Scenarios]
   *     summary: Retrieves information for up to 100 pricing scenarios.
   *     responses:
   *       200:
   *         description: List of scenarios
   */
  app.get(api.scenarios.list.path, async (req, res) => {
    const authHeader = req.headers.authorization;
     if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    const scenarios = await storage.getScenarios();
    res.json(scenarios);
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/scenarios/{id}:
   *   get:
   *     tags: [Scenarios]
   *     summary: Retrieves information for a specific pricing scenario.
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: integer
   *     responses:
   *       200:
   *         description: Single scenario
   */
  app.get(api.scenarios.get.path, async (req, res) => {
    const authHeader = req.headers.authorization;
     if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    const scenario = await storage.getScenario(Number(req.params.id));
    if (!scenario) {
      return res.status(404).json({ message: "Scenario not found" });
    }
    res.json(scenario);
  });

  /**
   * @openapi
   * /api/uwm/instantpricequote/v1/scenarios/{id}:
   *   delete:
   *     tags: [Scenarios]
   *     summary: Deletes a specific pricing scenario.
   *     parameters:
   *       - in: path
   *         name: id
   *         required: true
   *         schema:
   *           type: integer
   *     responses:
   *       204:
   *         description: Scenario deleted
   */
  app.delete(api.scenarios.delete.path, async (req, res) => {
    const authHeader = req.headers.authorization;
     if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    await storage.deleteScenario(Number(req.params.id));
    res.status(204).end();
  });

  return httpServer;
}
