# ZenSmart Executor - Design Guidelines

## Design Approach

**Selected Approach:** Design System (Material Design 3 with Google Search influences)
**Rationale:** The application requires Google-like simplicity with productivity tool functionality. Material Design 3 provides the clean, modern aesthetic while maintaining the familiar Google paradigm. The design balances minimal visual weight with powerful functionality.

## Core Design Principles

1. **Zen Simplicity:** Centered, spacious layout with generous whitespace
2. **Progressive Disclosure:** Advanced features revealed through expandable panels
3. **Instant Feedback:** Clear visual states for automation execution
4. **Familiar Patterns:** Google-like interaction models users already understand

## Layout System

### Spacing Primitives
Use Tailwind units: **2, 3, 4, 6, 8, 12, 16, 20, 24** for consistent rhythm throughout the application.

### Page Structure
```
┌─────────────────────────────────────────┐
│     Header (60px fixed)                  │
├────────┬────────────────────────────────┤
│        │                                 │
│ Sidebar│      Main Content Area          │
│ (280px)│      (Centered container)       │
│        │                                 │
│        │                                 │
└────────┴────────────────────────────────┘
```

**Header:** Fixed height 60px, spans full width, contains logo and theme toggle
**Sidebar:** Fixed width 280px when expanded, 0px when collapsed, overlay on mobile
**Main Content:** Max-width 800px, centered horizontally, padding-x of 16 on mobile, 24 on desktop
**Vertical Centering:** Main search interface vertically centered until results appear

## Typography System

### Font Family
- **Primary:** 'Inter' - clean, modern, excellent readability
- **Monospace:** 'JetBrains Mono' - for code snippets and technical output

### Hierarchy
- **Logo/Brand:** 32px, font-weight 700, letter-spacing tight
- **H1 (Page Title):** 24px, font-weight 600
- **H2 (Section Headers):** 18px, font-weight 600
- **H3 (Subsections):** 16px, font-weight 600
- **Body Large:** 16px, font-weight 400, line-height 1.6
- **Body Regular:** 14px, font-weight 400, line-height 1.5
- **Body Small:** 12px, font-weight 400, line-height 1.4
- **Code/Technical:** 13px, font-weight 400, monospace

## Component Library

### Search Input (Primary Interface)
- **Container:** Rounded-full (9999px), shadow-lg, backdrop-blur-sm
- **Height:** 56px on desktop, 48px on mobile
- **Padding:** px-6, py-3
- **Typography:** 16px body text
- **Icon Placement:** Leading search icon (20px), trailing submit button
- **States:** Subtle elevation increase on focus, smooth transitions
- **Width:** 600px max on desktop, full width minus 32px padding on mobile

### Sidebar Panel
- **Header Section:** 
  - Height: 60px (matches app header)
  - Brand identifier or section title
  - Collapse toggle button (24px icon)
- **Content Sections:**
  - Cache section: Scrollable list, max-height based on viewport
  - History section: Scrollable list below cache
  - Each item: 48px min-height, rounded-lg, hover state with subtle elevation
- **Dividers:** 1px separator between sections, margin-y 12px
- **Scroll Behavior:** Independent scroll areas for cache and history

### Settings Panel
- **Trigger:** Gear icon button in header (40px touch target)
- **Panel:** Dropdown/modal overlay, width 320px
- **Model Selection:**
  - Radio group with clear labels
  - Options: OpenAI GPT-4, Anthropic Claude, Google Gemini
  - 48px height per option, full-width clickable area
- **Additional Settings:** Stacked vertically, 16px spacing

### Theme Toggle
- **Button:** 40px × 40px touch target, rounded-full
- **Icons:** Sun (20px) and moon (20px), smooth cross-fade transition
- **Position:** Top-right corner of header, margin-right 16px
- **Animation:** 300ms rotation on toggle

### Execution Results Display
- **Container:** Rounded-lg, shadow-md, padding 16px
- **Layout:** 
  - Status badge at top (Running/Success/Error)
  - Action logs in chronological list
  - Extracted data in structured format (JSON-like presentation)
- **Log Items:** 
  - 40px min-height, rounded-md
  - Icon + timestamp + action description
  - Expandable for detailed information
- **Data Display:** Syntax-highlighted, scrollable, monospace font

### History/Cache Items
- **Item Structure:**
  - 48px min-height, rounded-lg
  - Padding: 12px 16px
  - Grid layout: icon (24px) | content (flex-grow) | timestamp/actions (auto)
- **Content:**
  - Primary text: 14px, font-weight 500, truncate
  - Secondary text: 12px, opacity-70, truncate
- **Actions:** Icon buttons (32px touch target) for rerun/delete
- **Hover State:** Subtle elevation, smooth transition

### Live Execution Indicator
- **Position:** Fixed bottom-right corner or floating below search
- **Container:** Rounded-lg, shadow-lg, padding 12px 16px
- **Content:**
  - Pulsing indicator dot (8px)
  - Status text (14px)
  - Minimal close button
- **Animation:** Fade in/out, slide up on appear

## Interaction Patterns

### Search Flow
1. **Initial State:** Centered search box, logo above, minimal interface
2. **Input Focus:** Subtle elevation, suggestions dropdown if history exists
3. **Execution:** Search moves to top, results area appears below
4. **Loading:** Animated indicator in search box, live status updates
5. **Completion:** Results display, search remains accessible at top

### Sidebar Behavior
- **Desktop:** Toggle between 280px (open) and 0px (closed)
- **Mobile:** Overlay with backdrop, slide-in animation from left
- **Transition:** 250ms ease-in-out
- **Collapsed State:** Thin indicator strip (4px) on left edge with hover expand

### Theme Transition
- **Duration:** 300ms for all elements
- **Properties:** background, text colors, shadows, borders
- **Preservation:** User preference saved to localStorage

## Responsive Breakpoints

- **Mobile:** < 768px - Single column, sidebar overlay, stacked layout
- **Tablet:** 768px - 1024px - Collapsible sidebar, reduced max-widths
- **Desktop:** > 1024px - Full layout with expanded sidebar by default

## Animation Guidelines

**Use Sparingly:** Only for meaningful state changes
- **Search focus:** 150ms ease-out
- **Sidebar toggle:** 250ms ease-in-out
- **Theme switch:** 300ms ease-in-out
- **Results appear:** 200ms fade-in with slight slide-up
- **Loading states:** Subtle pulse/shimmer, no aggressive spinners

## Accessibility

- **Keyboard Navigation:** Full keyboard support, visible focus indicators (2px outline, 4px offset)
- **ARIA Labels:** Descriptive labels for all interactive elements
- **Screen Readers:** Proper semantic HTML, live regions for status updates
- **Focus Management:** Logical tab order, focus trapping in modals
- **Contrast:** Ensure WCAG AA compliance minimum

## Key Screens Layout

### 1. Initial/Empty State
- Vertically and horizontally centered search box
- "ZenSmart Executor" logo above (40px margin-bottom)
- Tagline below logo: "Execute browser automations with natural language"
- Settings and theme toggle in fixed header

### 2. Active Execution State
- Search box moved to top (margin-top 24px)
- Sidebar visible with cache/history
- Live execution panel showing progress
- Results area displaying logs and data

### 3. Results View
- Search box at top, ready for new query
- Previous results scrollable below
- Action buttons: "Run Again", "Save to Cache", "Export Data"
- Related suggestions at bottom

## Technical Specifications

- **Container Max-Width:** 800px for main content, 1400px for full layout
- **Minimum Touch Targets:** 40px × 40px
- **Border Radius:** rounded-lg (8px) for cards, rounded-full for buttons/search
- **Elevation Levels:** 
  - Base: shadow-sm
  - Elevated: shadow-md
  - Floating: shadow-lg
  - Modal: shadow-xl

**Critical:** This interface must feel instantly familiar yet powerful. Every element serves a purpose. The design scales from simple one-prompt executions to complex multi-step automations without overwhelming the user.