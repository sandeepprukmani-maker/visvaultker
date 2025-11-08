# AutoPilot Studio X Design Guidelines

## Design Approach

**System-Based Approach**: Drawing from VS Code, Linear, and Chrome DevTools aesthetics - prioritizing information density, professional developer tooling, and functional clarity. This is a power-user application where efficiency and learnability trump visual flair.

**Core Design Principles**:
- Developer-tool aesthetics with clean, technical precision
- Information-dense layouts that maximize workspace
- Clear visual hierarchy for complex multi-panel interfaces
- Minimal decorative elements - every pixel serves a purpose

---

## Typography System

**Font Stack**: 
- UI Text: Inter (via Google Fonts CDN) - clean, readable at small sizes
- Code: JetBrains Mono (via Google Fonts CDN) - excellent for code display

**Type Scale**:
- Hero/Primary Headings: text-2xl to text-3xl, font-semibold
- Section Headings: text-lg, font-medium
- Body Text: text-sm, font-normal (default for most UI)
- Code/Technical: text-xs to text-sm, font-mono
- Labels/Meta: text-xs, font-medium, uppercase tracking-wide

---

## Layout System

**Spacing Primitives**: Use Tailwind units of **2, 3, 4, 6, 8** consistently
- Component padding: p-3, p-4, p-6
- Section spacing: space-y-4, gap-4, gap-6
- Tight groupings: space-y-2, gap-2
- Panel margins: m-0 (panels fill containers)

**Grid Architecture**:
- Multi-panel split-screen layout (60/40 or 50/50 splits)
- Resizable dividers between major sections
- Sidebar navigation: Fixed 240px-280px width
- Main workspace: Flexible with min/max constraints

---

## Component Library

### Navigation & Structure

**Primary Sidebar** (Left):
- Fixed width panel with icon + label navigation
- Icons from Heroicons (outline style)
- Sections: Dashboard, Tasks, Workflows, Recordings, Settings
- Active state: subtle border-l-2 indicator

**Top Toolbar**:
- height h-14, border-b-1
- Contains: Project name, execution controls (play/stop/record), user menu
- Action buttons with icon + text for primary actions

**Status Bar** (Bottom):
- height h-8, border-t-1  
- Real-time status indicators, execution time, current mode
- Right-aligned metadata (connection status, browser version)

### Core Panels

**Browser Preview Panel**:
- Full-height container with embedded iframe/screenshot view
- Top controls bar: URL input, back/forward, refresh, viewport selector
- Loading skeleton with pulsing animation during execution
- Screenshot overlays with click coordinates for recorded actions

**Code Editor Panel** (Monaco):
- Zero padding container for Monaco to fill completely
- Line numbers enabled, minimap on right
- Syntax highlighting for JavaScript/TypeScript
- Bottom status line showing language, line count

**Task Library Panel**:
- List view with search bar (h-10) at top
- Card-based tasks with: icon, title (text-sm font-medium), description (text-xs), metadata
- Grid layout: grid-cols-1 with gap-3
- Hover state reveals action buttons (edit, delete, duplicate, run)

**Workflow Builder**:
- Full canvas with React Flow integration
- Node cards: rounded-lg, p-4, with connection handles
- Floating toolbar for adding nodes (position: absolute, top-4, left-4)
- Mini-map in bottom-right corner

### Forms & Inputs

**AI Prompt Interface**:
- Large textarea (min-h-32) with placeholder guidance
- Submit button with loading state and spinner
- Generated plan preview below with step-by-step breakdown

**Input Fields**:
- Standard height h-10 for text inputs
- Labels: text-sm font-medium mb-2
- Help text: text-xs mt-1
- Form groups with space-y-4

### Buttons & Actions

**Primary Actions**:
- h-10 px-6 rounded-md font-medium
- Icons with text for clarity (Heroicons)

**Secondary/Ghost**:
- h-9 px-4 rounded-md font-normal
- Icon-only variants: w-9 h-9

**Icon Buttons** (Toolbar):
- w-9 h-9 square with centered icon
- Tooltip on hover for labels

### Data Display

**Execution Results**:
- Table layout with alternating row backgrounds
- Columns: Timestamp, Action, Status, Duration
- Status badges: px-2 py-1 rounded-full text-xs

**Screenshot Gallery**:
- Grid: grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4
- Images with aspect-video, rounded-lg, border-1
- Overlay caption on hover with filename and timestamp

**Task Cards**:
- p-4 rounded-lg border-1
- Header: icon (w-8 h-8) + title
- Description: text-sm line-clamp-2
- Footer: metadata chips and action menu

---

## Specialized Components

**Recording Indicator**:
- Floating badge (position: fixed, top-4, right-4)
- Pulsing red dot animation + "Recording..." text
- Stop button integrated

**Execution Timeline**:
- Horizontal stepper showing automation steps
- Connected nodes with status indicators (pending/running/complete/error)
- Current step highlighted with subtle glow

**Split Panel Divider**:
- w-1 cursor-col-resize with drag handle
- Hover state: slightly wider for discoverability

**Modal Overlays**:
- Max-w-2xl centered with backdrop blur
- Close button (top-right, w-8 h-8)
- Header: text-xl font-semibold, border-b, p-6
- Body: p-6, Footer: p-6 border-t with action buttons

---

## Animation Guidelines

**Minimize Motion** - Developer tools should feel instant:
- Panel transitions: none (instant layout changes)
- Loading states: subtle pulse on skeleton screens
- Button states: immediate feedback, no delays
- Exceptions: Recording indicator pulse, execution progress animations

---

## Accessibility

- All interactive elements keyboard navigable
- Focus rings visible and consistent (ring-2 ring-offset-2)
- ARIA labels for icon-only buttons
- Semantic HTML throughout
- High contrast text for readability in code-heavy interfaces

---

## Layout Examples

**Main Application View**:
```
[Sidebar 240px] [Browser Preview 50%] [Code Editor 50%]
[Status Bar spanning full width]
```

**Workflow Builder View**:
```
[Sidebar 240px] [Canvas with floating toolbar and mini-map]
```

**Task Management View**:
```
[Sidebar 240px] [Task Library grid with search] [Task Detail panel 30%]
```

---

This design creates a professional, efficient developer tool that prioritizes function over form while maintaining polish and usability.