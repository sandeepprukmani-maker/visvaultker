import { useScenarios, useDeleteScenario } from "@/hooks/use-scenarios";
import { Navbar } from "@/components/layout/Navbar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { format } from "date-fns";
import { Trash2, FileText, ArrowUpRight } from "lucide-react";
import { Link } from "wouter";
import { useAuth } from "@/hooks/use-auth";

export default function Scenarios() {
  const { data: scenarios, isLoading } = useScenarios();
  const deleteMutation = useDeleteScenario();
  const { isAuthenticated } = useAuth();

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);
  };

  if (!isAuthenticated) {
    return (
       <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
                <h2 className="text-2xl font-bold">Authentication Required</h2>
                <p className="text-muted-foreground">Please log in on the home page to view scenarios.</p>
                <Link href="/">
                    <Button>Go to Login</Button>
                </Link>
            </div>
        </div>
       </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-display font-bold text-slate-900">Scenario History</h1>
            <p className="text-lg text-slate-600 mt-2">Manage your saved quotes and previous calculations.</p>
          </div>
          <Link href="/">
            <Button>
                New Quote <ArrowUpRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
        </div>

        <Card className="shadow-lg border-0">
          <CardHeader className="border-b bg-white">
            <CardTitle>Recent Scenarios</CardTitle>
            <CardDescription>A list of all valid pricing scenarios generated.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : scenarios && scenarios.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/50">
                    <TableHead>Date</TableHead>
                    <TableHead>Borrower</TableHead>
                    <TableHead>Loan Amount</TableHead>
                    <TableHead>Credit Score</TableHead>
                    <TableHead>Zip Code</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scenarios.map((scenario) => (
                    <TableRow key={scenario.id} className="hover:bg-slate-50 transition-colors">
                      <TableCell className="font-medium">
                        {scenario.createdAt && format(new Date(scenario.createdAt), "MMM d, yyyy h:mm a")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                                {scenario.borrowerName.charAt(0)}
                            </div>
                            {scenario.borrowerName}
                        </div>
                      </TableCell>
                      <TableCell>{formatCurrency(scenario.loanAmount)}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            scenario.creditScore >= 740 ? "bg-green-100 text-green-700" : 
                            scenario.creditScore >= 680 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
                        }`}>
                            {scenario.creditScore}
                        </span>
                      </TableCell>
                      <TableCell>{scenario.propertyZipCode}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                            {/* In a real app, this would open details. For now just delete is implemented fully visually */}
                            <Button variant="ghost" size="icon" title="View Details">
                                <FileText className="w-4 h-4 text-muted-foreground" />
                            </Button>
                            
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="icon" className="hover:text-destructive hover:bg-destructive/10">
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Scenario?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This action cannot be undone. This will permanently delete the scenario for {scenario.borrowerName}.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction 
                                    className="bg-destructive hover:bg-destructive/90"
                                    onClick={() => deleteMutation.mutate(scenario.id)}
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                  <FileText className="w-8 h-8 text-slate-300" />
                </div>
                <h3 className="text-lg font-medium text-slate-900">No Scenarios Found</h3>
                <p className="text-slate-500 mt-2 max-w-sm">
                  You haven't generated any quotes yet. Go to the calculator to create your first scenario.
                </p>
                <Link href="/">
                    <Button className="mt-6" variant="outline">Go to Calculator</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
