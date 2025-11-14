import { TrendingDown, Clock, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import type { TokenMetrics as TokenMetricsType } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";

export function TokenMetrics() {
  const { data: metrics, isLoading } = useQuery<TokenMetricsType>({
    queryKey: ["/api/metrics"],
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-10 w-10 rounded-lg mb-6" />
              <Skeleton className="h-9 w-32 mb-2" />
              <Skeleton className="h-4 w-40 mb-2" />
              <Skeleton className="h-3 w-36" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-muted-foreground">No metrics available yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Total Tokens Used */}
      <Card data-testid="card-total-tokens">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
              <Zap className="w-5 h-5 text-primary" />
            </div>
          </div>
          <div className="mt-6">
            <p className="text-3xl font-bold" data-testid="text-total-tokens">
              {metrics.totalTokensUsed.toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground mt-1">Total Tokens Used</p>
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <span className="text-green-600">↓ {metrics.estimatedSavings}%</span>
              <span>vs unoptimized</span>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Cost Savings */}
      <Card data-testid="card-cost-savings">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/10">
              <TrendingDown className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <div className="mt-6">
            <p className="text-3xl font-bold" data-testid="text-savings-percentage">
              {metrics.estimatedSavings}%
            </p>
            <p className="text-sm text-muted-foreground mt-1">Tokens Saved</p>
            <p className="text-xs text-muted-foreground mt-2">
              Through prompt caching & batching
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Average Response Time */}
      <Card data-testid="card-avg-time">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div className="mt-6">
            <p className="text-3xl font-bold" data-testid="text-avg-time">
              {(metrics.averageExecutionTime / 1000).toFixed(1)}s
            </p>
            <p className="text-sm text-muted-foreground mt-1">Avg Response Time</p>
            <p className="text-xs text-muted-foreground mt-2">
              {metrics.totalExecutions} total executions
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
