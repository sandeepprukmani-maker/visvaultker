import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { mortgageQuoteRequestSchema, type MortgageQuoteRequest } from "@shared/schema";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Loader2, DollarSign, User, Home, Building2, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import { z } from "zod";

// Create a schema that handles coercions for the form specifically
// The schema from shared/schema.ts expects numbers, but inputs return strings
const formSchema = mortgageQuoteRequestSchema.extend({
  loanAmount: z.coerce.number().min(1000, "Minimum loan amount is $1,000"),
  salesPrice: z.coerce.number().min(1, "Required"),
  appraisedValue: z.coerce.number().min(1, "Required"),
  creditScore: z.coerce.number().min(300).max(850),
  monthlyIncome: z.coerce.number().min(0),
  propertyZipCode: z.string().min(5, "Zip code must be 5 digits"),
  // Set defaults for complex fields we aren't showing in the UI for simplicity
  loanTypeIds: z.array(z.string()).default(["1"]), // Default to Conventional
  purposeTypeId: z.string().default("1"), // Purchase
  propertyTypeId: z.string().default("1"), // Single Family
  occupancyTypeId: z.string().default("1"), // Primary Residence
});

type FormData = z.infer<typeof formSchema>;

interface QuoteFormProps {
  onSubmit: (data: MortgageQuoteRequest) => void;
  isLoading: boolean;
}

export function QuoteForm({ onSubmit, isLoading }: QuoteFormProps) {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      borrowerName: "",
      loanAmount: 350000,
      salesPrice: 400000,
      appraisedValue: 400000,
      creditScore: 740,
      monthlyIncome: 8500,
      propertyZipCode: "",
      loanTypeIds: ["1"],
      purposeTypeId: "1",
      propertyTypeId: "1",
      occupancyTypeId: "1",
    },
  });

  const handleSubmit = (data: FormData) => {
    // Cast back to the request type now that numbers are coerced
    onSubmit(data as unknown as MortgageQuoteRequest);
  };

  return (
    <Card className="border-0 shadow-lg bg-white/50 backdrop-blur-sm">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2.5 rounded-full">
            <CalculatorIcon className="w-6 h-6 text-primary" />
          </div>
          <div>
            <CardTitle className="text-xl">Mortgage Calculator</CardTitle>
            <CardDescription>Enter borrower details to get instant pricing</CardDescription>
          </div>
        </div>
      </CardHeader>
      <Separator className="mb-6" />
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              
              {/* Borrower Info Section */}
              <div className="col-span-1 md:col-span-2">
                <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2 mb-4">
                  <User className="w-4 h-4" /> Borrower Information
                </h3>
              </div>

              <FormField
                control={form.control}
                name="borrowerName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Borrower Name</FormLabel>
                    <FormControl>
                      <Input placeholder="John Doe" {...field} className="bg-white" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="creditScore"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Credit Score</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <TrendingUp className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input type="number" {...field} className="pl-9 bg-white" />
                      </div>
                    </FormControl>
                    <FormDescription>Range: 300 - 850</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="monthlyIncome"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monthly Income</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input type="number" {...field} className="pl-9 bg-white" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Property Info Section */}
              <div className="col-span-1 md:col-span-2 mt-2">
                <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2 mb-4">
                  <Home className="w-4 h-4" /> Property Details
                </h3>
              </div>

              <FormField
                control={form.control}
                name="propertyZipCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Zip Code</FormLabel>
                    <FormControl>
                      <Input placeholder="90210" maxLength={5} {...field} className="bg-white" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="salesPrice"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sales Price</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input type="number" {...field} className="pl-9 bg-white" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="loanAmount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loan Amount</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input type="number" {...field} className="pl-9 bg-white" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="purposeTypeId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loan Purpose</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-white">
                          <SelectValue placeholder="Select purpose" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">Purchase</SelectItem>
                        <SelectItem value="2">Refinance (Rate/Term)</SelectItem>
                        <SelectItem value="3">Refinance (Cash Out)</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="occupancyTypeId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Occupancy</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-white">
                          <SelectValue placeholder="Select occupancy" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">Primary Residence</SelectItem>
                        <SelectItem value="2">Second Home</SelectItem>
                        <SelectItem value="3">Investment Property</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

            </div>

            <Button 
              type="submit" 
              className="w-full h-12 text-lg font-semibold shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating Quote...
                </>
              ) : (
                "Get Instant Quote"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

function CalculatorIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="16" height="20" x="4" y="2" rx="2" />
      <line x1="8" x2="16" y1="6" y2="6" />
      <line x1="16" x2="16" y1="14" y2="18" />
      <path d="M16 10h.01" />
      <path d="M12 10h.01" />
      <path d="M8 10h.01" />
      <path d="M12 14h.01" />
      <path d="M8 14h.01" />
      <path d="M12 18h.01" />
      <path d="M8 18h.01" />
    </svg>
  );
}
