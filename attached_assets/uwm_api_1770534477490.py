from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union

app = FastAPI(
    title="UWM Public API: Instant Price Quote",
    description="API documentation for UWM Instant Price Quote based on the Onboarding Guide.",
    version="3.0"
)

# --- Models ---

# Authentication
class TokenRequest(BaseModel):
    grant_type: str = Field(..., description="Must be 'password' or 'refresh_token'")
    username: Optional[str] = Field(None, description="Required if grant_type is 'password'")
    password: Optional[str] = Field(None, description="Required if grant_type is 'password'")
    client_id: str
    client_secret: str
    scope: Optional[str] = Field(None, description="Required if grant_type is 'password'")
    refresh_token: Optional[str] = Field(None, description="Required if grant_type is 'refresh_token'")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    resource: str
    refresh_token: Optional[str] = None
    refresh_token_expires_in: Optional[int] = None
    id_token: str

class ErrorResponse(BaseModel):
    error: str
    error_description: Optional[str] = None
    message: Optional[str] = None

# Layouts
class LayoutRequest(BaseModel):
    PreScenarioId: Optional[str] = None
    ObfuscatedScenarioId: Optional[str] = None

class SelectListItem(BaseModel):
    id: str
    displayValue: str
    fieldValueDescription: Optional[str] = None

class LayoutItem(BaseModel):
    itemId: str
    label: str
    defaultValue: str
    isDisplay: bool
    isRequired: bool
    displayInputType: str
    selectListData: Optional[List[SelectListItem]] = None

class LayoutResponse(BaseModel):
    priceQuoteFilterItems: List[LayoutItem]

# Quotes
class MortgageQuoteRequest(BaseModel):
    brokerAlias: Optional[str] = None
    loanOfficer: Optional[str] = None
    loanAmount: float
    loanTypeIds: List[str]
    salesPrice: float
    appraisedValue: float
    purposeTypeId: str
    firstTimeHomeBuyer: Optional[bool] = None
    propertyTypeId: str
    occupancyTypeId: str
    propertyZipCode: str
    creditScore: int
    monthlyIncome: float
    borrowerName: str
    numberOfUnits: Optional[int] = None
    attachmentTypeId: Optional[str] = None
    prepaymentPenaltyId: Optional[str] = None
    numberOfFinancedProperties: Optional[int] = None
    leaseTypeId: Optional[str] = None
    isFirstTimeInvestor: Optional[bool] = None
    debtServiceCreditRatio: Optional[float] = None
    refinancePurposeID: Optional[str] = None
    mortgageInsuranceType: Optional[int] = None
    controlYourPrice: Optional[int] = Field(None, ge=0, le=40)

class QuotePricePoint(BaseModel):
    interestRate: dict
    adjustments: List[dict]
    principalAndInterest: dict
    monthlyPayment: dict
    mortgageInsurance: dict
    originationFee: Optional[dict]
    finalPrice: Optional[dict]
    finalPriceAfterOriginationFee: dict
    isBestQuotePricePoint: bool
    annualPercentageRate: float
    buydownSchedule: List[dict]
    amortizationTypeId: str
    paymentsPerYear: int
    numberOfPayments: int

class ValidQuoteItem(BaseModel):
    mortgageProductId: int
    mortgageProductName: str
    mortgageProductAlias: str
    loanToValue: float
    actualTermYears: int
    targetRate: float
    totalAdjustment: float
    customPricingMessaging: Optional[dict]
    quoteLoanDetails: List[Any]
    quotePricePoints: List[QuotePricePoint]
    productHighlights: List[dict]

class InvalidQuoteItem(BaseModel):
    mortgageProductId: int
    mortgageProductName: str
    mortgageProductAlias: str
    invalidReasons: List[str]
    failures: List[dict]
    errorMessages: Optional[List[str]]
    borrowerName: str
    legalDisclaimer: str
    obfuscatedScenarioId: int
    brokerage: dict
    loanOfficer: dict
    quotedDate: str
    effectiveDate: str
    commitmentPeriod: str

class QuoteResponse(BaseModel):
    loanAmount: float
    validQuoteItems: List[ValidQuoteItem]
    invalidQuoteItems: List[InvalidQuoteItem]
    errorMessages: Optional[List[str]] = None
    borrowerName: Optional[str] = None
    legalDisclaimer: Optional[str] = None
    obfuscatedScenarioId: Optional[int] = None
    brokerage: Optional[dict] = None
    loanOfficer: Optional[dict] = None
    quotedDate: Optional[str] = None
    effectiveDate: Optional[str] = None
    commitmentPeriod: Optional[str] = None

class HelocQuoteRequest(BaseModel):
    # Based on Mortgage fields + specific HELOC fields if any
    # Assuming similar structure for demo purposes as exact request body for HELOC wasn't fully parsed in snippet
    brokerAlias: Optional[str] = None
    loanOfficer: Optional[str] = None
    loanAmount: float
    # Add other fields as necessary based on full PDF analysis
    # For now, using a generic dict to allow flexibility
    propertyZipCode: str
    creditScore: int
    monthlyIncome: float
    borrowerName: str

# Scenarios
class ScenarioResponse(BaseModel):
    pass # Define based on PDF

# --- Endpoints ---

@app.post("/adfs/oauth2/token", response_model=TokenResponse, tags=["Authentication"])
async def create_token(request: TokenRequest):
    """
    Create a bearer token and refresh token.
    """
    return {
        "access_token": "dummy_token",
        "token_type": "bearer",
        "expires_in": 3600,
        "resource": "https://api.uwm.com/loanorigination",
        "refresh_token": "dummy_refresh_token",
        "refresh_token_expires_in": 57599,
        "id_token": "dummy_id_token"
    }

@app.post("/api/uwm/instantpricequote/v1/mortgagepricinglayout", response_model=LayoutResponse, tags=["Mortgage"])
async def get_mortgage_pricing_layout(
    request: LayoutRequest,
    authorization: str = Header(..., description="BEARER <token>")
):
    """
    Retrieves a partial list of components that must be specified to create a non-HELOC pricing scenario.
    """
    return {"priceQuoteFilterItems": []}

@app.post("/api/uwm/instantpricequote/v1/heloclayout", response_model=LayoutResponse, tags=["HELOC"])
async def get_heloc_layout(
    request: LayoutRequest,
    authorization: str = Header(..., description="BEARER <token>")
):
    """
    Retrieves a partial list of components that must be specified to create a HELOC pricing scenario.
    """
    return {"priceQuoteFilterItems": []}

@app.post("/api/uwm/instantpricequote/v1/pricequote", response_model=QuoteResponse, tags=["Mortgage"])
async def create_mortgage_price_quote(
    request: MortgageQuoteRequest,
    authorization: str = Header(..., description="BEARER <token>")
):
    """
    Creates a pricing scenario for a non-HELOC loan product.
    """
    return {
        "loanAmount": request.loanAmount,
        "validQuoteItems": [],
        "invalidQuoteItems": []
    }

@app.post("/api/uwm/instantpricequote/v1/helocquote", response_model=QuoteResponse, tags=["HELOC"])
async def create_heloc_price_quote(
    request: HelocQuoteRequest,
    authorization: str = Header(..., description="BEARER <token>")
):
    """
    Creates a pricing scenario for a HELOC loan product.
    Note: Endpoint URL is inferred as 'helocquote' based on naming conventions.
    """
    return {
        "loanAmount": request.loanAmount,
        "validQuoteItems": [],
        "invalidQuoteItems": []
    }

# Stub for Scenarios
@app.get("/api/uwm/instantpricequote/v1/scenarios", tags=["Scenarios"])
async def get_all_scenarios(authorization: str = Header(..., description="BEARER <token>")):
    """
    Retrieves information for up to 100 pricing scenarios created by the user in the past 30 days.
    """
    pass

@app.get("/api/uwm/instantpricequote/v1/scenarios/{scenario_id}", tags=["Scenarios"])
async def get_single_scenario(scenario_id: str, authorization: str = Header(..., description="BEARER <token>")):
    """
    Retrieves information for a specific pricing scenario created by the user in the past 30 days.
    """
    pass

@app.delete("/api/uwm/instantpricequote/v1/scenarios/{scenario_id}", tags=["Scenarios"])
async def delete_scenario(scenario_id: str, authorization: str = Header(..., description="BEARER <token>")):
    """
    Deletes one or more pricing scenarios.
    """
    pass

if __name__ == "__main__":
    import uvicorn
    # Run on 0.0.0.0:5000 for Replit
    uvicorn.run(app, host="0.0.0.0", port=5000)
