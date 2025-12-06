# Design Guidelines: Prompt-to-Browser Automation Tool

## Design Approach

**Selected Approach:** Design System-inspired with Developer Tool Aesthetics

**Primary References:** Linear (clean, functional UI), VS Code (developer familiarity), Vercel (modern web tools)

**Key Principles:**
- Functionality first: Clear hierarchy prioritizing the chat interface and execution feedback
- Developer-friendly: Familiar patterns from IDE and terminal interfaces
- Information clarity: Dense data presentation without overwhelming users
- Responsive feedback: Visual indicators for automation states

---

## Core Design Elements

### A. Typography

**Font Family:**
- Primary: 'Inter' from Google Fonts (UI text, buttons, labels)
- Monospace: 'JetBrains Mono' or 'Fira Code' from Google Fonts (logs, code, URLs)

**Hierarchy:**
- Page Title: text-2xl font-semibold
- Section Headers: text-lg font-medium
- Body Text: text-base font-normal
- Labels: text-sm font-medium
- Code/Logs: text-sm font-mono
- Captions: text-xs

---

### B. Layout System

**Spacing Units:** Use Tailwind's 4, 8, 12, 16, 24 units consistently (p-4, gap-8, mb-12, etc.)

**Container Structure:**
- Full viewport height application (h-screen)
- Two-column layout for desktop: 2/3 main area + 1/3 sidebar
- Single column stack for mobile
- Consistent padding: p-6 for containers, p-4 for cards

**Grid System:**
- Main workspace: flex or grid layouts
- Chat messages: flex-col with gap-4
- History items: divide-y for separation

---

### C. Component Library

**Navigation/Header:**
- Top bar with app branding and status indicators
- Height: h-14
- Includes: logo/title, connection status badge, settings icon

**Chat Interface (Primary):**
- Message bubbles: User prompts (right-aligned) vs System responses (left-aligned)
- Input area: Fixed bottom with textarea, send button
- Auto-scroll to latest message
- Timestamp labels for each message

**Execution Feedback Panel:**
- Real-time progress indicator (animated spinner or progress bar)
- Step-by-step action log with icons
- Current browser state display
- Success/error state indicators

**Browser Action Display:**
- Compact action cards showing: Action type, Target element, Status
- Icons from Heroicons for action types (cursor-click, pencil, eye, etc.)
- Collapsible details for advanced info

**History Sidebar:**
- List of past automation tasks
- Each item shows: Timestamp, Prompt summary, Status badge
- Click to view full details
- Search/filter functionality

**Status Indicators:**
- Connection status: Small badge with dot (connected/disconnected)
- Execution status: Loading spinner, success checkmark, error X
- Browser state: "Navigating...", "Waiting...", "Complete"

**Forms & Inputs:**
- Textarea for prompt input with placeholder text
- Auto-resize based on content
- Send button with keyboard shortcut hint
- Settings form with labeled inputs

---

### D. Animations

**Use sparingly:**
- Smooth scroll for chat messages (scroll-smooth)
- Fade-in for new messages (subtle opacity transition)
- Spinner for loading states (rotate animation)
- No unnecessary page transitions or decorative animations

---

## Application Layout Specifications

### Desktop Layout (lg and up):
```
┌─────────────────────────────────────────┐
│  Header/Status Bar                 (h-14)│
├──────────────────────┬──────────────────┤
│                      │                  │
│  Main Chat Area      │  History Sidebar │
│  (2/3 width)         │  (1/3 width)     │
│                      │                  │
│  - Prompt messages   │  - Past tasks    │
│  - Execution logs    │  - Quick access  │
│  - Action feedback   │  - Search        │
│                      │                  │
├──────────────────────┴──────────────────┤
│  Input Area (Textarea + Send)      (h-24)│
└─────────────────────────────────────────┘
```

### Mobile Layout:
- Stack vertically: Header → Chat → Input
- History accessible via modal/drawer
- Input area remains fixed at bottom

---

## Special Considerations

**Developer Tool Aesthetic:**
- Subtle borders, not heavy boxes
- Use of monospace fonts for technical content
- Code-like formatting for URLs and selectors
- Terminal-inspired color coding for status

**Interaction Patterns:**
- Click history item → loads into chat view
- Keyboard shortcuts: Enter to send, Cmd+K for quick actions
- Copy button for logs and results
- Expandable sections for detailed execution steps

**Empty States:**
- Welcome message with example prompts
- Placeholder when no history exists
- Clear call-to-action to get started

---

## Images

**No hero images required** - this is a functional tool, not a marketing page. Focus on interface clarity and usability.