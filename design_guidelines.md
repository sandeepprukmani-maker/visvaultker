# Design Guidelines: Stagehand Automation Studio

## Design Approach

**Reference-Based Approach**: Drawing inspiration from Linear's technical precision, Vercel's developer focus, and Stripe's polish. This is a utility-focused developer tool requiring efficiency and clarity.

## Core Design Principles

1. **Developer-First**: Clean, technical aesthetic with focus on code and automation workflows
2. **Real-time Feedback**: Immediate visual response to automation actions
3. **Information Density**: Maximize useful information without overwhelming
4. **Progressive Disclosure**: Show complexity only when needed

## Typography

**Font Families:**
- Primary: Inter (UI elements, labels, buttons)
- Code: JetBrains Mono (code blocks, selectors, logs)

**Hierarchy:**
- Page Title: 32px, semibold
- Section Headers: 20px, medium
- Body Text: 14px, regular
- Code/Logs: 13px, monospace
- Small Labels: 12px, medium

## Layout System

**Spacing Units**: Use Tailwind units of 2, 4, 6, 8, 12, 16, 24, 32
- Consistent: `p-4`, `gap-6`, `mb-8`, `mt-12`
- Element spacing: 4-6 units
- Section spacing: 12-16 units
- Page margins: 24-32 units

**Grid Structure:**
- Main container: `max-w-7xl mx-auto`
- Split-screen layout: 50/50 or 60/40 (input/output)
- Three-column for detailed views: 25/50/25 (config/preview/code)

## Component Library

### Navigation
- Top navigation bar with logo, status indicator, session controls
- Fixed height: `h-16`
- Subtle border-bottom separator

### Input Panel
- Prominent URL input field (full width, `h-12`)
- Natural language prompt textarea (`min-h-24`, auto-expand)
- Action mode selector (radio group: Act, Observe, Extract, Agent)
- Execute button (primary CTA, `h-10`)
- Configuration accordion (model selection, options)

### Automation Preview
- Live browser viewport display (iframe or screenshot)
- Overlay indicators for current action
- Element highlighting during observe mode
- Loading states with subtle animations

### Execution Log
- Scrollable timeline of actions (`max-h-96`, overflow-auto)
- Each log entry: timestamp, action type, status icon, description
- Expandable details for each step
- Visual connection lines between steps

### Code Output
- Syntax-highlighted code block
- Tab switcher: TypeScript | Cached | Agent
- Copy button (top-right corner)
- Download button
- Line numbers on left

### Status Indicators
- Badge components for: Running, Success, Error, Waiting
- Icon + text combinations
- Semantic styling (green, red, yellow, blue)

## Visual Patterns

### Cards
- Subtle border: `border border-neutral-200`
- Rounded corners: `rounded-lg`
- Internal padding: `p-6`
- Background: `bg-white`

### Code Blocks
- Dark theme for code: `bg-neutral-900`
- Light text: `text-neutral-100`
- Padding: `p-4`
- Scrollable: `overflow-x-auto`

### Forms
- Input fields: `h-10`, `px-3`, `rounded-md`, `border`
- Focus ring: `focus:ring-2 focus:ring-blue-500`
- Label above input: `mb-2`, `text-sm`, `font-medium`

### Buttons
- Primary: Solid, high contrast, `px-4 py-2`
- Secondary: Outlined, `border-2`
- Icon buttons: Square, `w-10 h-10`
- Disabled state: 40% opacity

## Page Layouts

### Main Automation View (Split Screen)

**Left Panel (40%):**
- URL input at top
- Natural language prompt textarea
- Mode selector (tabs or radio)
- Execute button
- Configuration section (collapsed by default)

**Right Panel (60%):**
- Top: Browser preview (60% height)
- Bottom: Execution log (40% height)
- Resizable divider between them

### Code Output View

Full-width code panel appears below when automation completes:
- Tab switcher for different formats
- Syntax highlighting
- Action buttons (Copy, Download, Re-run)

### Alternative: Three-Column Layout

**Left (30%):** Input controls
**Center (40%):** Live preview
**Right (30%):** Log + Code output (tabbed)

## Animations

**Minimal and purposeful:**
- Fade in: New log entries (150ms)
- Slide down: Expandable sections (200ms)
- Pulse: Active element indicator
- Progress bar: During automation execution

**No:**
- Elaborate transitions
- Decorative animations
- Carousel effects

## Images

**No hero image needed** - This is a utility-focused application tool. The interface itself is the hero.

**Icons:**
- Use Heroicons throughout for consistency
- 16px or 20px sizes
- Inline with text where appropriate

**Status Icons:**
- Checkmark: Success
- X: Error
- Clock: Waiting
- Arrow: In progress

## Specific Features

### Action Preview (Observe Mode)
- Highlight detected elements with subtle border
- Show action labels on hover
- Display confidence scores as small badges

### Selector Display
- Monospace font for XPath/CSS
- Inline copy button
- Syntax highlighting for selector type

### Session Controls
- Start/Stop buttons in header
- Session ID display
- Link to Browserbase session (if applicable)

### Model Selector
- Dropdown with popular models at top
- Grouped by provider (OpenAI, Anthropic, Google)
- CUA models marked with badge

## Responsive Behavior

**Desktop (primary):** Three-column or split layout
**Tablet:** Stack panels vertically, maintain readability
**Mobile:** Single column, collapsible sections

## Accessibility

- All interactive elements keyboard accessible
- Focus indicators on all inputs
- ARIA labels for icon-only buttons
- High contrast text (4.5:1 minimum)
- Screen reader announcements for status changes

## Professional Polish

- Consistent 8px grid alignment
- Uniform border radius (6px for cards, 4px for inputs)
- Cohesive elevation system (subtle shadows)
- Thoughtful empty states with helpful messages
- Error states with actionable guidance
- Loading skeletons for async content