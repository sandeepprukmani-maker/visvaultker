import { ThemeProvider } from "../theme-provider"
import { ThemeToggle } from "../theme-toggle"

export default function ThemeToggleExample() {
  return (
    <ThemeProvider>
      <div className="p-4">
        <ThemeToggle />
      </div>
    </ThemeProvider>
  )
}
