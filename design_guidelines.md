# ZenSmart Executor - Design Guidelines

## Design Approach
**Reference-Based**: Inspired by Google's radical simplicity philosophy - maximum functionality with minimal visual elements. Secondary influences from Linear's clean typography and Stripe's restrained elegance.

## Core Design Principles
1. **Extreme Minimalism**: Every pixel must justify its existence
2. **Focus-Driven**: The prompt input is the hero, everything else supports it
3. **Breathing Room**: Generous whitespace creates calm, focused environment
4. **Instant Clarity**: Users know exactly what to do within 2 seconds

---

## Typography System

**Primary Font**: Inter (via Google Fonts CDN)
**Secondary Font**: JetBrains Mono (for code/technical content)

**Hierarchy**:
- Logo/Brand: 2xl (24px), font-semibold
- Main Prompt Placeholder: base (16px), font-normal
- Section Headers: lg (18px), font-medium
- Body Text: base (16px), font-normal
- Code/Technical: sm (14px), font-mono
- Metadata/Timestamps: xs (12px), font-normal

---

## Layout System

**Spacing Primitives**: Use Tailwind units of **4, 6, 8, 12, 16** exclusively
- Micro spacing: p-4, gap-4
- Standard spacing: p-8, my-8
- Section spacing: py-12, py-16
- Large spacing: py-20 (for hero area only)

**Container Strategy**:
- Homepage hero: `max-w-2xl mx-auto` (640px max, centered)
- Results area: `max-w-4xl mx-auto` (896px max, allows more breathing room)
- Dashboard metrics: `max-w-6xl mx-auto` (1152px for multi-column layouts)

---

## Component Library

### 1. Homepage Hero (Google-Inspired)
**Layout**: Vertical centering using `min-h-screen flex items-center justify-center`

**Structure**:
- Logo/Product name: Centered, 60px top margin from center
- Tagline: Centered, 1-line description below logo (text-base)
- Main prompt input: Large search box, 48px height minimum
- CTA hint: Small text below input ("Press Enter or click 'Execute'")

**Prompt Input Specifications**:
- Width: w-full within max-w-2xl container
- Height: h-12 (48px)
- Padding: px-6 py-3
- Border: 1px solid with subtle shadow (shadow-sm on default, shadow-md on focus)
- Border radius: rounded-lg
- Font: text-base
- Placeholder: "What would you like to automate?"
- Icon: Small execute/play icon on right side (inside input)

### 2. Status Indicator
**Position**: Fixed top-right corner during execution
**Layout**: Inline flex with icon + text
**Components**:
- Animated spinner/pulse icon (12x12px)
- Status text: text-sm, font-medium
- Current step display: text-xs below main status
**Spacing**: p-4, gap-2

### 3. Results Display
**Appears below homepage hero after execution**

**Structure** (stacked vertically, gap-6):
1. **Success Header**
   - Checkmark icon + "Automation Complete"
   - Execution time metadata (text-xs)

2. **Executed Code Section**
   - Header: "Playwright Code Executed"
   - Code block: JetBrains Mono, text-sm
   - Syntax highlighting for JavaScript
   - Copy button (top-right of code block)
   - Background: subtle gray (like GitHub code blocks)
   - Padding: p-6, rounded-lg

3. **Page State/Output Section**
   - Header: "Current Page State"
   - Accessibility tree data or extracted content
   - Structured, readable format
   - Padding: p-6, rounded-lg

4. **Action Buttons Row**
   - "Run Again" button
   - "Save to History" button
   - "New Automation" button (clears and returns to prompt)
   - Layout: flex gap-4, justify-end

### 4. Action History (Modal/Slide-over)
**Trigger**: Icon button in top-right (when not executing)
**Layout**: Slide-over panel from right, w-96 (384px)

**Structure**:
- Header: "Automation History" with close button
- Search/filter input (text-sm, h-10)
- List of saved automations:
  - Each item: prompt preview (2 lines max, truncated)
  - Timestamp (text-xs)
  - Replay button (icon only)
  - Hover state: subtle background highlight
- Spacing: p-6 for panel, gap-3 for list items

### 5. Token Metrics Dashboard
**Position**: Accessible via "Metrics" link in header OR footer
**Layout**: Grid of metric cards

**Cards** (3-column grid on desktop, stacked on mobile):
1. **Total Tokens Used**: Large number + trend indicator
2. **Cost Savings**: Percentage saved vs unoptimized
3. **Avg Response Time**: Milliseconds

**Card Specifications**:
- Padding: p-6
- Border: 1px solid, rounded-lg
- Shadow: subtle shadow-sm
- Layout: Icon top-left, metric bottom-right
- Metric font: text-3xl font-bold
- Label: text-sm
- Trend: text-xs with arrow icon

### 6. Header (Minimal)
**Only visible on results/dashboard pages, NOT homepage**

**Layout**: Sticky top, backdrop-blur
- Logo/brand name (left)
- Navigation links (right): "New Automation" | "History" | "Metrics"
- Height: h-16 (64px)
- Padding: px-8

### 7. Buttons
**Primary Button** (Execute, Run Again):
- Height: h-12 (48px)
- Padding: px-8
- Border radius: rounded-lg
- Font: font-medium, text-base
- Shadow: shadow-sm default, shadow-md on hover

**Secondary Button** (Save, Cancel):
- Same dimensions as primary
- Border: 1px solid
- No fill background by default

**Icon Button** (History, Close):
- Size: h-10 w-10 (40x40px)
- Padding: p-2
- Rounded: rounded-lg
- Icon size: 20x20px

---

## Navigation & Flow

1. **Homepage** → Minimal (logo + prompt input only)
2. **Executing** → Status indicator appears, input disabled
3. **Results** → Results section animates in below hero
4. **History Modal** → Slides in from right, overlay backdrop
5. **Metrics Dashboard** → Full page OR modal, depending on complexity

---

## Icons
**Library**: Heroicons (outline style via CDN)
**Common Icons**:
- Execute: Play circle
- History: Clock
- Metrics: Chart bar
- Success: Check circle
- Error: X circle
- Copy: Clipboard
- Close: X mark
- Replay: Arrow path

---

## Animations
**Use very sparingly**:
- Input focus: Smooth shadow expansion (150ms)
- Button hover: Subtle scale (95% → 100%, 100ms)
- Status indicator: Pulse animation on icon only
- Results appear: Fade in + slide up (300ms)
- History panel: Slide in from right (200ms)

**No animations** on: Text, static content, backgrounds

---

## Responsive Behavior

**Desktop** (1024px+): All features visible as described

**Tablet** (768px - 1023px):
- Prompt input: Same prominence
- Metric cards: 2-column grid
- History panel: Full width overlay instead of slide-over

**Mobile** (< 768px):
- Prompt input: Full width minus 16px margins
- All cards: Single column stack
- Header links: Hamburger menu
- History: Full screen modal
- Code blocks: Horizontal scroll if needed

---

## Key Differentiators from Generic Designs

1. **Single-Input Focus**: Unlike multi-field forms, ONE input dominates
2. **No Sidebar**: Pure center-focused layout, history is hidden until needed
3. **Code Visibility**: Executed Playwright code always shown (transparency)
4. **Live Browser Window**: External (user sees real headed browser), not embedded iframe
5. **Accessibility Tree Data**: Shown in results as structured text, not hidden

---

## Images
**No images needed** - This is a tool/utility app, not marketing. The UI is purely functional minimalism.

**Exception**: Optional subtle pattern background (SVG noise texture, very low opacity) on homepage hero to add depth without clutter.

---

## Final Notes
- **White space is a feature**, not empty space
- Every interaction should feel **instant** (even with 2s latency, use optimistic UI updates)
- Typography does all the heavy lifting - **no decoration needed**
- The browser window running automation is the visual interest - **UI stays out of the way**