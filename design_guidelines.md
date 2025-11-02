# Design Guidelines: AI-Powered UI Automation System

## Design Approach

**Selected System**: Modern Developer Tools Aesthetic (Linear + Vercel + Playwright DevTools)

**Justification**: This is a technical automation platform for developers and QA engineers. The interface must prioritize information density, real-time feedback, and execution clarity while maintaining a polished, professional appearance. Drawing inspiration from Linear's crisp typography and Vercel's deployment dashboard precision, combined with Playwright's technical detail presentation.

**Core Principles**:
- Technical precision with visual polish
- Information hierarchy through contrast and spacing
- Real-time feedback visibility
- Command-first interaction model

---

## Typography

**Font Families**:
- Primary: Inter (via Google Fonts) - headings, UI elements, command input
- Monospace: JetBrains Mono (via Google Fonts) - code, selectors, logs, technical data

**Hierarchy**:
- Page Titles: text-2xl font-semibold tracking-tight
- Section Headers: text-lg font-medium
- Command Input: text-base font-normal (Inter)
- Body Text: text-sm
- Technical Data/Logs: text-sm font-mono (JetBrains Mono)
- Metadata Labels: text-xs uppercase tracking-wide font-medium
- Status Indicators: text-xs font-medium

---

## Layout System

**Spacing Primitives**: Tailwind units of 2, 4, 6, 8, 12, 16

**Standard Patterns**:
- Section padding: p-6 to p-8
- Card padding: p-4 to p-6
- Grid gaps: gap-4 or gap-6
- Component spacing: space-y-4 or space-y-6
- Tight groupings: space-y-2

**Container Strategy**:
- Full-width dashboard with sidebar: Main content max-w-7xl
- Centered modals/dialogs: max-w-2xl
- Code/log viewers: Full available width with horizontal scroll

---

## Component Library

### Navigation & Layout

**Sidebar Navigation** (Left-aligned, Fixed):
- Width: w-64
- Sections: Dashboard, Crawl, Automations, Pages, Elements, Settings
- Navigation items with icon (Heroicons) + label
- Active state: subtle background treatment
- Collapsed state support for more workspace

**Top Command Bar**:
- Fixed at top, spans full width
- Prominent natural language input field (large, accessible)
- Recent commands dropdown
- Execute button with loading state
- Quick action buttons (New Crawl, View History)

**Main Content Area**:
- Two-column split where appropriate: 60/40 or 70/30 ratio
- Left: Primary content (logs, execution steps, page list)
- Right: Contextual details (element metadata, page screenshot, configuration)

### Core Components

**Command Input Interface**:
- Large textarea-style input with placeholder: "Enter command: 'Login as admin' or 'Add a new user'..."
- Auto-suggest dropdown showing similar past commands
- Syntax hints below input
- Submit button with loading/executing states
- Command history sidebar (Recent 10 commands with status badges)

**Crawl Configuration Panel**:
- URL input with validation
- Crawl depth selector (slider or number input)
- Advanced options accordion (screenshot quality, wait times, selectors)
- Start Crawl CTA button
- Real-time progress indicator during crawl

**Page Visualization Grid**:
- Masonry or standard grid layout (grid-cols-2 lg:grid-cols-3)
- Each card shows: thumbnail screenshot, page title, URL path, element count
- Hover reveals: quick actions (View Details, Re-crawl, Test Automation)
- Template grouping indicator (badge showing "5 similar pages")
- Click to expand into detailed view

**Execution Log Viewer**:
- Console-style log output with monospace font
- Step-by-step execution breakdown:
  - Timestamp (text-xs text-muted)
  - Action description (text-sm)
  - Screenshot thumbnail (click to expand)
  - Success/Error status badge
- Auto-scroll to latest during execution
- Filter controls: Show All / Errors Only / Warnings
- Export log button

**Element Metadata Panel** (Right sidebar or modal):
- Element preview: Screenshot with highlighted bounding box
- Selector strategies listed:
  - ID, Name, Text, Role, XPath, CSS selector
  - Confidence score for each (visual indicator)
- Element properties table (tag, attributes, text content)
- Similar elements section (vector similarity matches)
- Test selector button (validates if still exists)

**Automation Status Dashboard**:
- Hero metrics at top (large numbers):
  - Pages Crawled, Elements Indexed, Automations Run, Success Rate
- Recent automation runs table:
  - Command, Timestamp, Duration, Status, Actions Count
  - Click to view detailed execution
- Active/Queued automations with progress bars
- System health indicators (API status, browser pool, vector DB)

**Smart Forms**:
- Two-column layout for form fields (label left, input right) on desktop
- Single column on mobile
- Input fields with clear labels and validation states
- Helper text below inputs
- Required field indicators
- Submit/Cancel button group (right-aligned)

### Data Display

**Tables**:
- Striped rows for readability (alternating subtle background)
- Fixed header on scroll
- Sortable columns (icon indicators)
- Compact row height (efficient space usage)
- Hover state on rows
- Action icons in last column (aligned right)
- Pagination or infinite scroll for large datasets

**Status Badges**:
- Success: green treatment, checkmark icon
- Running/In Progress: blue treatment, spinner icon
- Warning: amber treatment, alert icon
- Error/Failed: red treatment, X icon
- Queued: gray treatment, clock icon
- Rounded, compact (text-xs font-medium)

**Code/Selector Display**:
- Monospace font in code blocks
- Syntax highlighting for selectors (CSS, XPath)
- Copy-to-clipboard button on hover
- Inline background treatment for distinction
- Line numbers for multi-line code

**Progress Indicators**:
- Linear progress bars for crawls and executions
- Percentage display (e.g., "45/100 pages crawled")
- Estimated time remaining
- Indeterminate state for unknown duration

### Overlays

**Modal Dialogs**:
- Centered overlay with backdrop blur
- Compact width for confirmations (max-w-md)
- Wide for detailed views (max-w-4xl)
- Header with title and close button
- Content area with appropriate spacing
- Footer with action buttons (right-aligned)

**Slideover Panels** (for element details, settings):
- Slide from right
- Full height
- Width: w-96 or w-1/3
- Close button and header
- Scrollable content area
- Sticky footer if needed

**Toasts/Notifications**:
- Top-right positioning
- Auto-dismiss after 4-5 seconds
- Action button for critical notifications
- Icon indicating type (success/error/info)
- Stack multiple notifications vertically

---

## Animations

**Minimal, Purposeful Animations**:
- Page transitions: Subtle fade (150ms)
- Dropdown reveals: Slide + fade (200ms)
- Loading states: Spinner or skeleton screens (no elaborate animations)
- Status changes: Subtle color transition (300ms)
- Hover states: Quick opacity/transform (100ms)

**No Scroll Animations**: This is a utility tool—avoid parallax or scroll-triggered effects

---

## Images

**Screenshot Integration**:
- Page thumbnails in grid: aspect-ratio-video (16:9), cover fit
- Full screenshots in details: Natural aspect, max height limit with scroll
- Element highlights: Bounding box overlay on screenshots
- Placeholder treatment: Skeleton loader or simple icon if screenshot unavailable

**No Hero Image**: This dashboard doesn't need marketing hero imagery. Instead, lead with the command input interface and real-time dashboard metrics.

**Visual Element Previews**:
- Inline element screenshots showing context (where element appears on page)
- Screenshot comparison for before/after crawl updates
- Visual diff highlighting for detected changes

---

## Distinctive Features

**Command-First Interface**:
- Spotlight-style command palette (CMD+K to activate)
- Natural language as primary interaction method
- Visual feedback showing AI interpretation of command

**Real-Time Execution Visualization**:
- Live browser preview (optional iframe showing automation running)
- Step-by-step action highlighting
- Simultaneous log output

**Intelligent Suggestions**:
- "Did you mean?" suggestions when command unclear
- Auto-complete for common actions based on learned pages
- Contextual help tooltips

**Visual Page Relationships**:
- Template grouping visualization (similar pages clustered)
- Site map view showing crawled page hierarchy
- Element relationship graph (optional advanced feature)

This design creates a powerful, technical dashboard that feels fast, precise, and intelligent—perfect for developers who need to command complex automation with simple language.