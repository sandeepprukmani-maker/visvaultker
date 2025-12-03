# Design Guidelines: Eko Web Automation Application

## Design Approach

**System-Based with Modern Accents**
Foundation: Material Design principles for productivity-focused UI with custom Eko branding integration
Justification: Utility-focused application requiring clarity and efficiency, enhanced with distinctive AI-forward visual identity

**Key Principles:**
- Clarity over decoration - every element serves the automation workflow
- Progressive disclosure - advanced features accessible without overwhelming beginners
- Real-time feedback - users always know what the system is doing
- Professional confidence - enterprise-ready aesthetic with modern touches

## Core Design Elements

### A. Typography

**Font Family:** Inter (primary), JetBrains Mono (code/logs)
- Headlines: Inter 600 (28px-36px)
- Section titles: Inter 600 (20px-24px)  
- Body text: Inter 400 (16px)
- Button text: Inter 500 (14px-16px)
- Code/logs: JetBrains Mono 400 (14px)
- Input placeholders: Inter 400 (16px)

### B. Layout System

**Spacing Primitives:** Tailwind units of 2, 4, 6, and 8
- Component padding: p-6 to p-8
- Section spacing: space-y-6 to space-y-8
- Card spacing: p-6
- Grid gaps: gap-4 to gap-6
- Button padding: px-6 py-2 to px-8 py-4

**Container Strategy:**
- Main container: max-w-7xl mx-auto
- Narrow content: max-w-3xl mx-auto
- Full-width panels: w-full with inner max-w-7xl

### C. Component Library

**Core Components:**

1. **Navigation Bar**
   - Fixed top position with subtle bottom border
   - Logo left, action buttons right
   - Height: h-16
   - Contains: Eko logo, "New Automation" button, history icon, settings

2. **Prompt Input Section** (Hero Replacement)
   - Large, centered text area with rounded corners
   - Floating label: "Describe your automation task..."
   - Template quick-actions below (pill buttons)
   - Example prompts shown as subtle suggestions
   - Gradient accent border on focus
   - Height: Auto-expanding, min-h-32

3. **Template Cards Grid**
   - 3-column grid (lg:grid-cols-3 md:grid-cols-2)
   - Cards with icon, title, description, "Use Template" button
   - Hover: subtle lift effect (shadow increase)
   - Templates: "Web Scraping", "Form Automation", "Data Extraction", "Multi-step Research"

4. **Workflow Visualization Panel**
   - Expandable/collapsible card design
   - Shows dependency tree as connected nodes
   - Each step: icon, step name, status indicator
   - Parallel steps shown side-by-side
   - Sequential steps shown vertically connected
   - Active step highlighted with accent gradient

5. **Execution Status Card**
   - Fixed/sticky position during execution
   - Progress bar with percentage
   - Current step highlighted
   - Pause/Resume/Stop buttons (icon + text)
   - Real-time log stream (scrollable, monospace font)

6. **History Panel** (Side Drawer)
   - Slide-in from right
   - List of past executions with timestamp
   - Each item: task description, status badge, timestamp, "View Details" link
   - Filter by status (All, Success, Failed, In Progress)

7. **Form Elements**
   - Text inputs: Rounded borders, clean focus states
   - Buttons: Primary (gradient), Secondary (outline), Tertiary (ghost)
   - Toggle switches for advanced options
   - Dropdown selects with search for model selection

**Button System:**
- Primary: Gradient background (purple to blue), rounded-lg, shadow-sm
- Secondary: Border with transparent background, hover fills with subtle gradient
- Danger: Red theme for interrupt/cancel actions
- Icon buttons: Circular, minimal, hover background

**Status Indicators:**
- Planning: Animated pulse, purple dot
- Executing: Animated spinner, blue
- Paused: Yellow dot
- Completed: Green checkmark
- Failed: Red X

### D. Animations

**Minimal, purposeful only:**
- Workflow node connections: Subtle draw-in animation on plan generation (1s)
- Status transitions: Smooth fade between states (200ms)
- Panel slides: Side drawer entrance (300ms ease-out)
- Button hovers: Quick scale (150ms)
- NO scroll-triggered animations
- NO decorative background animations

## Layout Architecture

**Main Application Structure:**

```
┌─────────────────────────────────────┐
│         Navigation Bar              │
├─────────────────────────────────────┤
│                                     │
│     Prompt Input (Centered)         │
│     [Large text area]               │
│     [Template pills]                │
│                                     │
├─────────────────────────────────────┤
│                                     │
│   Quick Templates Grid (3-col)      │
│   [Card] [Card] [Card]              │
│   [Card] [Card] [Card]              │
│                                     │
├─────────────────────────────────────┤
│                                     │
│   Workflow Visualization            │
│   (Expandable, shown after plan)    │
│                                     │
├─────────────────────────────────────┤
│                                     │
│   Execution Status                  │
│   (Appears during execution)        │
│                                     │
└─────────────────────────────────────┘
```

**Responsive Behavior:**
- Desktop (lg): 3-column template grid, side-by-side workflow nodes
- Tablet (md): 2-column grid, stacked workflow nodes
- Mobile: Single column, collapsible panels by default

## Eko Brand Integration

**Visual Accent Elements:**
- Gradient: Purple (#8B5CF6) to Blue (#3B82F6) for primary actions
- Logo area: Subtle gradient background behind Eko wordmark
- Active state indicators: Gradient borders/backgrounds
- Success states: Gradient green (#10B981 to #06B6D4)

**Professional Constraints:**
- No excessive gradients - use sparingly for CTAs and accents only
- Maintain high contrast for readability
- Keep workflow visualization clean and technical-looking
- Logs/code areas: Pure monochrome for clarity

## Images

**No hero image needed.** This is a utility application where the prompt input is the hero element.

**Icon Usage:**
- Use Heroicons throughout for consistency
- Workflow step icons: Contextual (browser, file, search, etc.)
- Status icons: Standard (play, pause, stop, check, alert)
- Template cards: Large icons (h-12 w-12) to represent automation type

## Key User Experience Patterns

1. **Progressive Disclosure:** Advanced options (model selection, agent configuration) in collapsible "Advanced Settings" panel
2. **Immediate Feedback:** As user types prompt, show "AI analyzing..." indicator after 2s pause
3. **Workflow Transparency:** Always show what Eko is planning before execution starts
4. **Error States:** Clear error messages with suggested fixes, never just "Error"
5. **Empty States:** When no history, show illustration with "Start your first automation" CTA

## Accessibility

- All interactive elements: Minimum 44px touch target
- Focus indicators: Visible outline on all focusable elements
- Color contrast: WCAG AA minimum on all text
- Keyboard navigation: Tab order follows visual hierarchy
- Screen reader labels: All icons have aria-labels

This design creates a professional, efficient automation interface that balances technical capability with approachability, allowing both novice and advanced users to harness Eko's power effectively.