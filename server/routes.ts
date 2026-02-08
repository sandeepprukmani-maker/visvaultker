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

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  const swaggerOptions = {
    definition: {
      openapi: "3.0.0",
      info: {
        title: "UWM Public API: Instant Price Quote",
        description: "API documentation for UWM Instant Price Quote based on the Onboarding Guide.",
        version: "3.0",
      },
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
      // Validate input (though we return dummy data regardless)
      api.auth.token.input.parse(req.body);

      const response: z.infer<typeof tokenResponseSchema> = {
        access_token: "dummy_token_" + Math.random().toString(36).substring(7),
        token_type: "bearer",
        expires_in: 3600,
        resource: "https://api.uwm.com/loanorigination",
        refresh_token: "dummy_refresh_token",
        refresh_token_expires_in: 57599,
        id_token: "dummy_id_token"
      };
      
      res.json(response);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ error: "invalid_request", error_description: err.errors[0].message });
      }
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
    if (!authHeader || !authHeader.startsWith("BEARER ")) {
       // Note: In a real app we'd return 401, but keeping logic consistent with mock
       // For strict compliance with shared/routes:
       return res.status(401).json({ message: "Unauthorized" });
    }

    const response: z.infer<typeof layoutResponseSchema> = {
      priceQuoteFilterItems: [] // Returning empty list as per Python stub
    };
    res.json(response);
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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    const response: z.infer<typeof layoutResponseSchema> = {
      priceQuoteFilterItems: []
    };
    res.json(response);
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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }

    try {
      const input = api.quotes.mortgage.input.parse(req.body);

      // Generate a mock response based on input
      // We'll create one valid item and one invalid item to show UI capabilities
      
      const mockValidItem = {
        mortgageProductId: 101,
        mortgageProductName: "30 Year Fixed",
        mortgageProductAlias: "30Y FXD",
        loanToValue: (input.loanAmount / input.appraisedValue) * 100,
        actualTermYears: 30,
        targetRate: 6.5,
        totalAdjustment: 0.25,
        quoteLoanDetails: [],
        quotePricePoints: [
          {
            interestRate: { value: 6.5, display: "6.500%" },
            adjustments: [{ description: "Credit Score Adjustment", value: -0.125 }],
            principalAndInterest: { value: (input.loanAmount * 0.00632).toFixed(2) }, // Rough calc
            monthlyPayment: { value: (input.loanAmount * 0.007).toFixed(2) },
            mortgageInsurance: { value: 0 },
            finalPriceAfterOriginationFee: { value: 99.5 },
            isBestQuotePricePoint: true,
            annualPercentageRate: 6.65,
            buydownSchedule: [],
            amortizationTypeId: "Fixed",
            paymentsPerYear: 12,
            numberOfPayments: 360
          }
        ],
        productHighlights: [{ text: "Most Popular" }]
      };

      const mockResponse: z.infer<typeof quoteResponseSchema> = {
        loanAmount: input.loanAmount,
        validQuoteItems: [mockValidItem],
        invalidQuoteItems: [], // Keeping simple for now
        borrowerName: input.borrowerName,
        quotedDate: new Date().toISOString()
      };

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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    // Stub implementation
    const response: z.infer<typeof quoteResponseSchema> = {
      loanAmount: req.body.loanAmount || 0,
      validQuoteItems: [],
      invalidQuoteItems: []
    };
    res.json(response);
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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
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
     if (!authHeader || !authHeader.startsWith("BEARER ")) {
        return res.status(401).json({ message: "Unauthorized" });
     }
    await storage.deleteScenario(Number(req.params.id));
    res.status(204).end();
  });

  return httpServer;
}
