import { useLatestPost, usePosters } from "@/hooks/use-posts";
import { LatestNewsCard } from "@/components/LatestNewsCard";
import { PosterGallery } from "@/components/PosterGallery";
import { Header } from "@/components/Header";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

export default function Home() {
  const { data: latestPost, isLoading: isLoadingPost, error: postError } = useLatestPost();
  const { data: posters, isLoading: isLoadingPosters } = usePosters();

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Header />
      
      <main className="container mx-auto px-4 py-8 md:py-12 space-y-16">
        {/* Hero Section - Latest News */}
        <section className="max-w-4xl mx-auto space-y-8">
          <div className="space-y-2 text-center">
            <h1 className="text-4xl md:text-5xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-700 pb-2">
              Market Intelligence
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Real-time mortgage rate analysis and automated social media content generation for loan officers.
            </p>
          </div>

          {isLoadingPost ? (
            <div className="space-y-4 bg-card rounded-2xl p-6 border shadow-sm">
              <div className="flex gap-2">
                <Skeleton className="h-6 w-32 rounded-full" />
              </div>
              <Skeleton className="h-12 w-3/4" />
              <Skeleton className="h-4 w-1/4" />
              <div className="space-y-2 pt-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
              <div className="pt-6 flex gap-4">
                <Skeleton className="h-12 w-48 rounded-xl" />
                <Skeleton className="h-12 w-32 rounded-xl" />
              </div>
            </div>
          ) : postError ? (
            <div className="rounded-2xl bg-destructive/5 border border-destructive/20 p-8 text-center space-y-4">
              <div className="bg-destructive/10 w-12 h-12 rounded-full flex items-center justify-center mx-auto text-destructive">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-destructive">Failed to Load Market Data</h3>
              <p className="text-muted-foreground">We couldn't fetch the latest mortgage news. Please try again later.</p>
            </div>
          ) : latestPost ? (
            <LatestNewsCard post={latestPost} />
          ) : null}
        </section>

        {/* Gallery Section */}
        <section className="space-y-8">
          <div className="flex items-center justify-between border-b pb-4">
            <div>
              <h2 className="text-3xl font-display font-bold">Content Library</h2>
              <p className="text-muted-foreground mt-1">Your generated social media captions</p>
            </div>
            <div className="text-sm text-muted-foreground font-medium bg-secondary px-3 py-1 rounded-full">
              {posters?.length || 0} Captions Created
            </div>
          </div>

          {isLoadingPosters ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-4">
                  <Skeleton className="aspect-[4/5] w-full rounded-xl" />
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ))}
            </div>
          ) : posters ? (
            <PosterGallery posters={posters} />
          ) : null}
        </section>
      </main>
    </div>
  );
}
