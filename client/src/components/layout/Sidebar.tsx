import { useState } from "react";
import { motion } from "framer-motion";
import { Terminal, Play, Clock, Settings, Database, Cpu, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const [active, setActive] = useState("run");

  const navItems = [
    { id: "run", icon: Play, label: "Run Agent" },
    { id: "workflows", icon: Layers, label: "Workflows" },
    { id: "history", icon: Clock, label: "History" },
    { id: "knowledge", icon: Database, label: "Knowledge" },
    { id: "settings", icon: Settings, label: "Settings" },
  ];

  return (
    <div className="h-screen w-16 md:w-64 bg-sidebar border-r border-white/10 flex flex-col justify-between py-6 transition-all duration-300">
      <div>
        <div className="px-4 md:px-6 mb-8 flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shadow-[0_0_15px_rgba(124,58,237,0.5)]">
            <Cpu className="h-5 w-5 text-white" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight hidden md:block">
            EKO<span className="text-primary">.ai</span>
          </span>
        </div>

        <nav className="space-y-2 px-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group relative overflow-hidden",
                active === item.id 
                  ? "bg-white/5 text-primary shadow-inner" 
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              {active === item.id && (
                <motion.div
                  layoutId="active-pill"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_var(--color-primary)]"
                />
              )}
              <item.icon className={cn("h-5 w-5", active === item.id && "animate-pulse")} />
              <span className="font-medium hidden md:block">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="px-4 md:px-6">
        <div className="p-4 rounded-xl bg-gradient-to-br from-primary/20 to-purple-900/20 border border-primary/20 hidden md:block">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-mono text-primary uppercase tracking-wider">System Online</span>
          </div>
          <div className="h-1 w-full bg-black/50 rounded-full overflow-hidden">
            <div className="h-full bg-primary w-[70%]" />
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-muted-foreground font-mono">
            <span>CPU: 42%</span>
            <span>MEM: 1.2GB</span>
          </div>
        </div>
      </div>
    </div>
  );
}
