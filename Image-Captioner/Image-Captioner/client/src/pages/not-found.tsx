import { Link } from "wouter";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#FFC107] text-[#004D40] p-4">
      <div className="max-w-md w-full bg-white shadow-[12px_12px_0px_0px_rgba(0,77,64,1)] p-8 md:p-12 text-center border-4 border-[#004D40]">
        <div className="mb-6 flex justify-center">
          <AlertTriangle className="h-24 w-24 text-[#004D40]" strokeWidth={2.5} />
        </div>
        
        <h1 className="font-display font-black text-6xl mb-2 tracking-tighter">404</h1>
        <div className="h-1 w-24 bg-[#004D40] mx-auto mb-6" />
        
        <p className="text-xl font-bold mb-8 uppercase tracking-wide">Page Not Found</p>
        
        <p className="text-[#004D40]/80 mb-8 font-medium leading-relaxed">
          The quote you are looking for has been lost in the void. It may have never existed, or perhaps it was just too profound for this reality.
        </p>

        <Link href="/">
          <Button className="w-full">Return to Safety</Button>
        </Link>
      </div>
    </div>
  );
}
