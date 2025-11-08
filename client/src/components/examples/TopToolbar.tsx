import { TopToolbar } from '../TopToolbar';
import { SidebarProvider } from "@/components/ui/sidebar";
import { ThemeProvider } from "next-themes";

export default function TopToolbarExample() {
  return (
    <ThemeProvider attribute="class" defaultTheme="light">
      <SidebarProvider>
        <TopToolbar 
          isRunning={false}
          isRecording={false}
          onRun={() => console.log('Run')}
          onStop={() => console.log('Stop')}
          onRecord={() => console.log('Record')}
        />
      </SidebarProvider>
    </ThemeProvider>
  );
}
