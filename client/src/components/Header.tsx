import { Link } from "wouter";
import { TrendingUp, FileImage } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="bg-primary/10 p-2 rounded-lg group-hover:bg-primary/20 transition-colors">
            <TrendingUp className="w-6 h-6 text-primary" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight">
            Mortgage<span className="text-primary">Pulse</span>
          </span>
        </Link>
        
        <nav className="flex items-center gap-6">
          <Link href="/" className="text-sm font-medium hover:text-primary transition-colors">
            Dashboard
          </Link>
          <a 
            href="https://www.mortgagenewsdaily.com/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
          >
            Source
          </a>
        </nav>
      </div>
    </header>
  );
}
