import { useState } from "react";
import { QuoteForm } from "@/components/QuoteForm";
import { QuoteResults } from "@/components/QuoteResults";
import { useAuth } from "@/hooks/use-auth";
import { useMortgageQuote } from "@/hooks/use-quotes";
import { type MortgageQuoteRequest, type QuoteResponse } from "@shared/schema";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/layout/Navbar";
import { Lock, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const { isAuthenticated, login, isLoggingIn } = useAuth();
  const quoteMutation = useMortgageQuote();
  const [quoteData, setQuoteData] = useState<QuoteResponse | null>(null);

  const handleQuoteSubmit = (data: MortgageQuoteRequest) => {
    setQuoteData(null); // Reset previous results
    quoteMutation.mutate(data, {
      onSuccess: (data) => {
        setQuoteData(data);
        // Scroll to results
        setTimeout(() => {
          document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    });
  };

  // Login Screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md"
          >
            <Card className="shadow-2xl border-t-4 border-t-primary">
              <CardContent className="pt-8 text-center space-y-6">
                <div className="bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                  <Lock className="w-8 h-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <h1 className="text-2xl font-bold font-display">Broker Portal Access</h1>
                  <p className="text-muted-foreground">Please authenticate to access the pricing engine.</p>
                </div>
                
                <div className="p-4 bg-slate-50 rounded-lg text-sm text-left border mb-4">
                  <p className="font-semibold mb-1 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-green-600" />
                    Staging Credentials
                  </p>
                  <p className="text-muted-foreground">Using UWM staging credentials for instant pricing.</p>
                </div>

                <Button 
                  size="lg" 
                  className="w-full font-semibold" 
                  onClick={() => login({})}
                  disabled={isLoggingIn}
                >
                  {isLoggingIn ? "Authenticating..." : "Connect to Pricing Engine"}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <header className="mb-8">
          <h1 className="text-3xl font-display font-bold text-slate-900">Instant Pricing</h1>
          <p className="text-lg text-slate-600 mt-2">Generate accurate mortgage quotes in seconds.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-5 xl:col-span-4 space-y-6 sticky top-24">
            <QuoteForm onSubmit={handleQuoteSubmit} isLoading={quoteMutation.isPending} />
          </div>

          <div className="lg:col-span-7 xl:col-span-8 min-h-[500px]" id="results-section">
            <AnimatePresence mode="wait">
              {quoteData ? (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <QuoteResults quote={quoteData} />
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-slate-200 rounded-xl bg-white/50"
                >
                  <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                    <ShieldCheck className="w-8 h-8 text-slate-300" />
                  </div>
                  <h3 className="text-lg font-medium text-slate-900">Ready to Price</h3>
                  <p className="text-slate-500 max-w-sm mt-2">
                    Enter the loan details on the left to generate real-time pricing scenarios and product options.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}
