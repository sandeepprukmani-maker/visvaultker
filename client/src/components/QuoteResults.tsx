import { type QuoteResponse } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, AlertCircle, Calendar, DollarSign, Percent, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

interface QuoteResultsProps {
  quote: QuoteResponse;
}

export function QuoteResults({ quote }: QuoteResultsProps) {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };

  const formatPercent = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "percent",
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    }).format(val / 100); // Assuming rate comes as 4.5 for 4.5% or 0.045 depending on API, assuming standard fractional
  };

  // Helper to ensure we render something even if rates object structure is complex
  const getRate = (rateObj: any) => {
    // Assuming rateObj is just the number value or an object with value
    if (typeof rateObj === "object" && rateObj !== null) return rateObj.value || 0;
    return Number(rateObj) || 0;
  };

  return (
    <div className="space-y-6">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="border-l-4 border-l-primary shadow-md">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-2xl font-bold text-primary">Quote Summary</CardTitle>
                <CardDescription>
                  Loan Amount: <span className="font-semibold text-foreground">{formatCurrency(quote.loanAmount)}</span>
                  {quote.borrowerName && <span> • Borrower: {quote.borrowerName}</span>}
                </CardDescription>
              </div>
              <Badge variant="outline" className="px-3 py-1 text-sm font-medium">
                {quote.validQuoteItems.length} Products Found
              </Badge>
            </div>
          </CardHeader>
        </Card>
      </motion.div>

      <Tabs defaultValue="valid" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="valid" className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            Valid Options ({quote.validQuoteItems.length})
          </TabsTrigger>
          <TabsTrigger value="invalid" className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            Invalid Options ({quote.invalidQuoteItems.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="valid" className="space-y-4">
          {quote.validQuoteItems.length === 0 ? (
            <div className="text-center py-12 bg-white/50 rounded-lg border border-dashed">
              <p className="text-muted-foreground">No valid loan products found for this scenario.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {quote.validQuoteItems.map((item, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-200">
                    <CardHeader className="bg-slate-50 dark:bg-slate-900 border-b pb-3">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Badge className="bg-primary/90 hover:bg-primary">{item.mortgageProductAlias}</Badge>
                          <span className="font-medium text-sm text-muted-foreground">{item.actualTermYears} Year Term</span>
                        </div>
                        <Badge variant="secondary" className="font-mono">ID: {item.mortgageProductId}</Badge>
                      </div>
                      <CardTitle className="mt-2 text-lg">{item.mortgageProductName}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Interest Rate</p>
                          <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-bold text-primary">
                              {/* Taking the first price point as example best rate */}
                              {item.quotePricePoints[0] ? formatPercent(getRate(item.quotePricePoints[0].interestRate) * 100) : "N/A"}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            APR: {item.quotePricePoints[0] ? formatPercent(item.quotePricePoints[0].annualPercentageRate) : "N/A"}
                          </p>
                        </div>
                        
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Monthly P&I</p>
                          <div className="flex items-baseline gap-1">
                            <span className="text-3xl font-bold text-foreground">
                               {item.quotePricePoints[0] ? formatCurrency(getRate(item.quotePricePoints[0].principalAndInterest)) : "N/A"}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">Excludes taxes & insurance</p>
                        </div>

                        <div className="flex flex-col justify-center">
                          <Button className="w-full gap-2 group">
                            View Amortization 
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                          </Button>
                        </div>
                      </div>

                      {/* Adjustments Preview */}
                      {item.quotePricePoints[0]?.adjustments && item.quotePricePoints[0].adjustments.length > 0 && (
                         <div className="mt-4 pt-4 border-t">
                            <p className="text-xs font-medium mb-2">Price Adjustments:</p>
                            <div className="flex flex-wrap gap-2">
                              {item.quotePricePoints[0].adjustments.slice(0, 3).map((adj, i) => (
                                <Badge key={i} variant="outline" className="text-xs font-normal">
                                  {/* Render adjustment description if available, otherwise generic */}
                                  Adjustment {i + 1}
                                </Badge>
                              ))}
                              {item.quotePricePoints[0].adjustments.length > 3 && (
                                <span className="text-xs text-muted-foreground self-center">+ {item.quotePricePoints[0].adjustments.length - 3} more</span>
                              )}
                            </div>
                         </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="invalid" className="space-y-4">
           {quote.invalidQuoteItems.map((item, idx) => (
             <Card key={idx} className="bg-red-50/30 border-red-100">
               <CardHeader>
                 <CardTitle className="text-base text-red-900">{item.mortgageProductName}</CardTitle>
               </CardHeader>
               <CardContent>
                 <ul className="list-disc list-inside space-y-1">
                   {item.invalidReasons.map((reason, i) => (
                     <li key={i} className="text-sm text-red-700">{reason}</li>
                   ))}
                   {(!item.invalidReasons || item.invalidReasons.length === 0) && (
                     <li className="text-sm text-red-700">Product criteria not met based on input parameters.</li>
                   )}
                 </ul>
               </CardContent>
             </Card>
           ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
