import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "../app-sidebar";

export default function AppSidebarExample() {
  return (
    <SidebarProvider>
      <AppSidebar />
    </SidebarProvider>
  );
}
