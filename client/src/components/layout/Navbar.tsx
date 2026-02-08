import { Link, useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { 
  Calculator, 
  History, 
  LogOut, 
  LayoutDashboard,
  Menu,
  X 
} from "lucide-react";
import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function Navbar() {
  const [location] = useLocation();
  const { logout, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (path: string) => location === path;
  
  const navItems = [
    { name: "Get Quote", path: "/", icon: Calculator },
    { name: "Scenarios", path: "/scenarios", icon: History },
  ];

  return (
    <nav className="border-b bg-white/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center gap-2 cursor-pointer">
              <div className="bg-primary p-2 rounded-lg">
                <LayoutDashboard className="h-5 w-5 text-white" />
              </div>
              <span className="font-display font-bold text-xl text-primary tracking-tight">
                RateEngine
              </span>
            </Link>
            
            <div className="hidden md:ml-10 md:flex md:space-x-8">
              {isAuthenticated && navItems.map((item) => (
                <Link key={item.path} href={item.path}>
                  <div className={`
                    inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium h-16 transition-colors cursor-pointer
                    ${isActive(item.path) 
                      ? "border-primary text-primary" 
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"}
                  `}>
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <div className="hidden md:flex items-center gap-2">
                  <span className="text-sm text-gray-500">Authenticated as Broker</span>
                  <Button variant="ghost" size="sm" onClick={logout} className="text-destructive hover:text-destructive/90 hover:bg-destructive/10">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </Button>
                </div>
                
                {/* Mobile Menu */}
                <div className="md:hidden">
                  <Sheet open={isOpen} onOpenChange={setIsOpen}>
                    <SheetTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <Menu className="h-6 w-6" />
                      </Button>
                    </SheetTrigger>
                    <SheetContent side="right">
                      <div className="flex flex-col gap-4 mt-8">
                        {navItems.map((item) => (
                          <Link key={item.path} href={item.path} onClick={() => setIsOpen(false)}>
                            <div className={`
                              flex items-center p-3 rounded-lg text-sm font-medium cursor-pointer
                              ${isActive(item.path) 
                                ? "bg-primary/10 text-primary" 
                                : "text-gray-500 hover:bg-gray-50"}
                            `}>
                              <item.icon className="w-5 h-5 mr-3" />
                              {item.name}
                            </div>
                          </Link>
                        ))}
                        <Button variant="outline" onClick={() => { logout(); setIsOpen(false); }} className="w-full justify-start text-destructive hover:text-destructive">
                          <LogOut className="w-4 h-4 mr-2" />
                          Sign Out
                        </Button>
                      </div>
                    </SheetContent>
                  </Sheet>
                </div>
              </>
            ) : (
              <Button size="sm" variant="outline" disabled>Not Signed In</Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
