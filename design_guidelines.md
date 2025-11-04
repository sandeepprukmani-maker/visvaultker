# Design Guidelines: AI Browser Automation Platform

## Design Approach

**Selected Approach:** Design System Hybrid (Material Design + Developer Tools Aesthetic)

**Rationale:** This is a production-grade automation platform for power users and developers. The design combines Material Design's robust component patterns with the clean, information-dense aesthetic of modern developer tools (VS Code, Chrome DevTools) and productivity applications (Linear, Notion).

**Core Principles:**
1. **Information Clarity** - Complex automation data presented with crystal-clear hierarchy
2. **Efficient Workflows** - Minimize clicks, maximize visibility of critical information
3. **Professional Polish** - Enterprise-grade appearance that inspires confidence
4. **Spatial Economy** - Dense information layouts without feeling cramped

---

## Typography System

**Font Stack:**
- **Primary:** Inter (headings, UI elements, buttons)
- **Monospace:** JetBrains Mono (code, selectors, logs, JSON output)

**Type Scale:**
- **Hero/Page Titles:** text-4xl (36px), font-bold
- **Section Headers:** text-2xl (24px), font-semibold
- **Subsection Headers:** text-xl (20px), font-semibold
- **Card Titles:** text-lg (18px), font-medium
- **Body Text:** text-base (16px), font-normal
- **Secondary/Meta:** text-sm (14px), font-normal
- **Micro Labels:** text-xs (12px), font-medium, uppercase tracking-wide
- **Code/Technical:** text-sm (14px), font-mono

**Hierarchy Rules:**
- Page titles always paired with subtitle/description (text-base, reduced opacity)
- Section headers use 80% opacity, subsections 100%
- All caps labels only for category tags and status badges

---

## Layout System

**Spacing Primitives:** Tailwind units of **2, 4, 6, 8, 12, 16**
- Component padding: p-4 to p-6
- Section spacing: py-8 to py-16
- Card gaps: gap-4 to gap-6
- Inline spacing: space-x-2 to space-x-4

**Grid Structure:**

**Main Dashboard Layout:**
- Sidebar navigation: w-64 (256px), fixed, full height
- Main content area: flex-1, max-w-7xl, mx-auto, px-8
- Three-column dashboard grid: grid-cols-3, gap-6

**Content Containers:**
- Full-width sections: w-full
- Content cards: Contained within max-w-7xl
- Form layouts: max-w-3xl for readability
- Code/technical displays: max-w-full (allow horizontal scroll if needed)

**Responsive Breakpoints:**
- Mobile (< 768px): Single column, collapsible sidebar
- Tablet (768-1024px): Two columns where applicable
- Desktop (1024px+): Full multi-column layouts

---

## Component Library

### Navigation Components

**Sidebar Navigation:**
- Fixed left sidebar, w-64
- Logo/brand at top with p-6
- Navigation sections grouped with dividers
- Nav items: px-4 py-2, rounded-lg, with icon + label
- Active state: full-width highlight, font-semibold
- Collapsible sections for sub-navigation

**Top Bar:**
- Fixed top, h-16, border-b
- Left: Breadcrumb navigation (text-sm, with separators)
- Right: Search bar, notifications icon, user avatar
- Search: w-64, rounded-full, with icon prefix

### Core UI Elements

**Cards:**
- Rounded-xl (12px radius)
- Border: 1px solid
- Padding: p-6
- Shadow: Subtle elevation (shadow-sm on hover → shadow-md)
- Header section with title + actions
- Content section with natural padding
- Optional footer for metadata/actions

**Buttons:**
- Primary: px-6 py-3, rounded-lg, font-medium
- Secondary: Same dimensions, outlined variant
- Icon buttons: p-2, rounded-lg, icon-only
- Button groups: Joined with rounded corners on ends only
- Sizes: sm (py-2 px-4), base (py-3 px-6), lg (py-4 px-8)

**Form Inputs:**
- Height: h-11 for all text inputs
- Padding: px-4
- Border radius: rounded-lg
- Labels: text-sm, font-medium, mb-2
- Helper text: text-xs, mt-1
- Consistent focus states with ring

**Status Badges:**
- Inline-flex, items-center
- px-3 py-1, rounded-full
- text-xs, font-medium, uppercase
- Icon prefix (8x8 dot or icon)
- Variants: Success, Warning, Error, Info, Neutral

### Data Display Components

**Execution Dashboard:**
- Split view: Left (browser preview) 60% | Right (execution log) 40%
- Browser preview: Full-height iframe/canvas with border-2
- Execution log: Scrollable, font-mono, line-height-relaxed
- Progress indicator: Full-width bar at top, animated
- Step cards: Collapsible accordion, showing current/completed/pending states

**DOM Tree Viewer:**
- Hierarchical tree structure with indent levels (pl-4 per level)
- Expandable nodes with chevron icons
- Element badges showing tag name (rounded, text-xs, font-mono)
- Hover states reveal selectors and attributes
- Search/filter bar at top

**Workflow Builder:**
- Canvas area: min-h-screen, grid pattern background
- Task nodes: Cards (w-64) with icon, title, description
- Connection lines: SVG paths between nodes
- Drag handles visible on hover
- Toolbar: Fixed top with task templates

**Task Library Grid:**
- grid-cols-3 on desktop, gap-6
- Each card shows: Icon (top), Title, Description (truncated), Metadata (date, run count)
- Hover effect: Slight lift (translate-y-1), shadow increase
- Quick actions on hover: Run, Edit, Delete icons

**Learned Website Profiles:**
- List view with expandable details
- Profile card shows: Site favicon, URL, element count, last updated
- Expanded view: Categorized element list, interaction graph preview
- Version history timeline on side panel

### Overlays & Modals

**Modal Dialogs:**
- Centered, max-w-2xl for standard, max-w-4xl for complex
- Backdrop: Semi-transparent overlay
- Content: p-8, rounded-2xl
- Header: Title + close button, border-b, pb-4
- Footer: Actions aligned right, border-t, pt-4

**Slide-over Panels:**
- Fixed right, w-96 for info panels, w-2/3 for detailed views
- Animated slide-in from right
- Used for: Element inspector, task details, settings

**Toast Notifications:**
- Fixed top-right, stacked vertically
- w-96, p-4, rounded-lg, shadow-lg
- Icon + message + close button
- Auto-dismiss after 5s, dismissible manually

---

## Specialized Sections

### Hero/Welcome Section (First-time Users)
- Full viewport height on initial load
- Centered content: max-w-4xl
- Headline: text-5xl, font-bold, mb-4
- Subheading: text-xl, mb-8
- Primary CTA: Large button (text-lg, px-8 py-4)
- Secondary action: Text link below
- Animated illustration or browser mockup (right side, 40% width)

### LLM Configuration Panel
- Table layout showing all models
- Columns: Model Name (font-mono), Provider, Capabilities (badges), Status (toggle)
- Edit button per row opens inline form
- Config file viewer: Monaco editor component, font-mono, syntax highlighting

### Real-time Execution View
- Fullscreen mode available
- Dual-pane: Live browser (left/main) + AI reasoning (right sidebar, w-80)
- Timeline scrubber showing execution steps
- Pause/Resume/Stop controls in floating toolbar
- Console output at bottom (collapsible, h-48 default)

### Workflow Visual Designer
- Node-based editor with zoom/pan controls
- Task palette (left sidebar, w-64): Drag-and-drop task templates
- Canvas: Infinite scroll, grid guides
- Properties panel (right, w-80): Shows selected node details
- Mini-map (bottom-right corner, 200x150px)

---

## Images & Visual Elements

**Images:**
- Hero illustration: Abstract representation of browser automation (nodes connected with data flowing), placed right side of hero text
- Dashboard screenshots: Mockups showing the tool in action for marketing sections
- Element inspector: Screenshots of learned website profiles with overlay annotations
- No background images - solid backgrounds only

**Icons:**
- Primary icon library: Heroicons (outline for navigation, solid for emphasis)
- 20x20 for inline icons, 24x24 for standalone icons
- Consistent stroke width across all icons

**Illustrations:**
- Workflow diagrams: Simple node-and-edge graphs
- Connection lines: Curved bezier paths, 2px stroke
- State indicators: Circular nodes with icons

---

## Animations

**Minimal, Purposeful Motion:**
- Page transitions: Fade-in only (duration-200)
- Card hovers: Scale-102, shadow elevation (duration-150)
- Loading states: Pulse animation on skeleton loaders
- Execution progress: Smooth linear progress bar animation
- **No** parallax, no scroll-triggered animations, no decorative motion

**Exceptions (where animation adds value):**
- Live execution: Real-time browser preview updates
- DOM tree: Smooth expand/collapse (duration-200)
- Workflow canvas: Node dragging with smooth repositioning

---

## Accessibility & Consistency

- All interactive elements minimum 44x44px touch target
- Form inputs maintain consistent h-11 throughout
- Focus states: 2px ring with offset
- Skip navigation link at top
- ARIA labels on icon-only buttons
- Keyboard navigation fully supported (tab order, shortcuts)
- High contrast text ratios maintained
- Screen reader announcements for status changes

---

This design creates a professional, information-dense automation platform that prioritizes clarity, efficiency, and production-grade polish. The aesthetic balances modern developer tool sensibilities with enterprise application robustness.