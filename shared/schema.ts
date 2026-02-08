import { pgTable, text, serial, integer, boolean, timestamp, jsonb, real } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// === TABLE DEFINITIONS ===

// We'll store the scenarios that are created
export const scenarios = pgTable("scenarios", {
  id: serial("id").primaryKey(),
  loanAmount: real("loan_amount").notNull(),
  borrowerName: text("borrower_name").notNull(),
  creditScore: integer("credit_score").notNull(),
  propertyZipCode: text("property_zip_code").notNull(),
  rawRequest: jsonb("raw_request").notNull(), // Store the full request details
  rawResponse: jsonb("raw_response").notNull(), // Store the calculated quote
  createdAt: timestamp("created_at").defaultNow(),
});

// === SCHEMAS ===

// Token Request
export const tokenRequestSchema = z.object({
  grant_type: z.string().describe("Must be 'password' or 'refresh_token'"),
  username: z.string().optional(),
  password: z.string().optional(),
  client_id: z.string(),
  client_secret: z.string(),
  scope: z.string().optional(),
  refresh_token: z.string().optional(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_in: z.number(),
  resource: z.string(),
  refresh_token: z.string().optional(),
  refresh_token_expires_in: z.number().optional(),
  id_token: z.string(),
});

// Layouts
export const layoutRequestSchema = z.object({
  PreScenarioId: z.string().optional(),
  ObfuscatedScenarioId: z.string().optional(),
});

export const selectListItemSchema = z.object({
  id: z.string(),
  displayValue: z.string(),
  fieldValueDescription: z.string().optional(),
});

export const layoutItemSchema = z.object({
  itemId: z.string(),
  label: z.string(),
  defaultValue: z.string(),
  isDisplay: z.boolean(),
  isRequired: z.boolean(),
  displayInputType: z.string(),
  selectListData: z.array(selectListItemSchema).optional(),
});

export const layoutResponseSchema = z.object({
  priceQuoteFilterItems: z.array(layoutItemSchema),
});

// Quotes
export const mortgageQuoteRequestSchema = z.object({
  brokerAlias: z.string().optional(),
  loanOfficer: z.string().optional(),
  loanAmount: z.number(),
  loanTypeIds: z.array(z.string()),
  salesPrice: z.number(),
  appraisedValue: z.number(),
  purposeTypeId: z.string(),
  firstTimeHomeBuyer: z.boolean().optional(),
  propertyTypeId: z.string(),
  occupancyTypeId: z.string(),
  propertyZipCode: z.string(),
  creditScore: z.number().int(),
  monthlyIncome: z.number(),
  borrowerName: z.string(),
  numberOfUnits: z.number().int().optional(),
  attachmentTypeId: z.string().optional(),
  prepaymentPenaltyId: z.string().optional(),
  numberOfFinancedProperties: z.number().int().optional(),
  leaseTypeId: z.string().optional(),
  isFirstTimeInvestor: z.boolean().optional(),
  debtServiceCreditRatio: z.number().optional(),
  refinancePurposeID: z.string().optional(),
  mortgageInsuranceType: z.number().int().optional(),
  controlYourPrice: z.number().min(0).max(40).optional(),
});

export const helocQuoteRequestSchema = z.object({
  brokerAlias: z.string().optional(),
  loanOfficer: z.string().optional(),
  loanAmount: z.number(),
  propertyZipCode: z.string(),
  creditScore: z.number().int(),
  monthlyIncome: z.number(),
  borrowerName: z.string(),
  // Generic fields for flexibility as per Python stub
  additionalData: z.record(z.any()).optional(),
});

// Response sub-models
export const quotePricePointSchema = z.object({
  interestRate: z.record(z.any()),
  adjustments: z.array(z.record(z.any())),
  principalAndInterest: z.record(z.any()),
  monthlyPayment: z.record(z.any()),
  mortgageInsurance: z.record(z.any()),
  originationFee: z.record(z.any()).optional(),
  finalPrice: z.record(z.any()).optional(),
  finalPriceAfterOriginationFee: z.record(z.any()),
  isBestQuotePricePoint: z.boolean(),
  annualPercentageRate: z.number(),
  buydownSchedule: z.array(z.record(z.any())),
  amortizationTypeId: z.string(),
  paymentsPerYear: z.number(),
  numberOfPayments: z.number(),
});

export const validQuoteItemSchema = z.object({
  mortgageProductId: z.number(),
  mortgageProductName: z.string(),
  mortgageProductAlias: z.string(),
  loanToValue: z.number(),
  actualTermYears: z.number(),
  targetRate: z.number(),
  totalAdjustment: z.number(),
  customPricingMessaging: z.record(z.any()).optional(),
  quoteLoanDetails: z.array(z.any()),
  quotePricePoints: z.array(quotePricePointSchema),
  productHighlights: z.array(z.record(z.any())),
});

export const invalidQuoteItemSchema = z.object({
  mortgageProductId: z.number(),
  mortgageProductName: z.string(),
  mortgageProductAlias: z.string(),
  invalidReasons: z.array(z.string()),
  failures: z.array(z.record(z.any())),
  errorMessages: z.array(z.string()).optional(),
  borrowerName: z.string(),
  legalDisclaimer: z.string(),
  obfuscatedScenarioId: z.number(),
  brokerage: z.record(z.any()),
  loanOfficer: z.record(z.any()),
  quotedDate: z.string(),
  effectiveDate: z.string(),
  commitmentPeriod: z.string(),
});

export const quoteResponseSchema = z.object({
  loanAmount: z.number(),
  validQuoteItems: z.array(validQuoteItemSchema),
  invalidQuoteItems: z.array(invalidQuoteItemSchema),
  errorMessages: z.array(z.string()).optional(),
  borrowerName: z.string().optional(),
  legalDisclaimer: z.string().optional(),
  obfuscatedScenarioId: z.number().optional(),
  brokerage: z.record(z.any()).optional(),
  loanOfficer: z.record(z.any()).optional(),
  quotedDate: z.string().optional(),
  effectiveDate: z.string().optional(),
  commitmentPeriod: z.string().optional(),
});

export const errorResponseSchema = z.object({
  error: z.string(),
  error_description: z.string().optional(),
  message: z.string().optional(),
});

// Database Types
export const insertScenarioSchema = createInsertSchema(scenarios);
export type InsertScenario = z.infer<typeof insertScenarioSchema>;
export type Scenario = typeof scenarios.$inferSelect;

// Export Types for API
export type TokenRequest = z.infer<typeof tokenRequestSchema>;
export type TokenResponse = z.infer<typeof tokenResponseSchema>;
export type LayoutRequest = z.infer<typeof layoutRequestSchema>;
export type LayoutResponse = z.infer<typeof layoutResponseSchema>;
export type MortgageQuoteRequest = z.infer<typeof mortgageQuoteRequestSchema>;
export type HelocQuoteRequest = z.infer<typeof helocQuoteRequestSchema>;
export type QuoteResponse = z.infer<typeof quoteResponseSchema>;
