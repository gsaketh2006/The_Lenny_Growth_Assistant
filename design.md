# UI/UX Design Specification (`design.md`)
# Project: The Lenny Growth Assistant
**Author:** Forward Deployed Engineering (FDE) Team  
**Status:** Approved & Implemented

---

## 1. Design Philosophy & Product Experience

The Lenny Growth Assistant is designed for high-performing product leaders, founders, and growth engineers who need rapid, dense, and rigorously verified insights. The interface balances high-density information architecture with clean typography, dark-mode ergonomics, and real-time verifiable trust signals.

### Core Principles:
1. **Verifiable Trust First:** Every assistant assertion must be visually backed by explicit grounding confidence badges and interactive source citation drawers.
2. **Actionable Artifact Workflow:** Generated strategic essays and growth experiment cards are treated as first-class, interactive, sandboxed documents displayed side-by-side with conversation context.
3. **Zero-Distraction Dark Ergonomics:** Dark palette (`#0b0f19` canvas) with Lenny brand orange accents (`#ee771b`), high-contrast typography, and fluid responsive panel scaling.
4. **Strict Isolation by Default:** All untrusted LLM HTML and dynamic CSS are quarantined within sandboxed `<iframe>` boundaries without compromising parent application security.

---

## 2. Information Architecture & Layout Structure

```
+-----------------------------------------------------------------------------------------------+
|                                    APPLICATION WORKSPACE                                      |
+---------------------+---------------------------------------+---------------------------------+
| SESSION SIDEBAR     | CHAT CONVERSATION AREA                | ARTIFACT VIEWER (Sandboxed)     |
| [w-72 / fixed]      | [flex-1 / scrollable]                 | [w-1/2 or Fullscreen toggle]    |
|                     |                                       |                                 |
| - Lenny Brand Logo  | - Status & Engine Bar (OLLAMA/CLAUDE) | - Title & Type Badge            |
| - [+ New Session]   | - Message Stream                      | - [Preview] / [Source] Switcher |
| - Sessions History  |   * User Bubble (Gradient Orange)     | - [Copy] [Download] [Fullscreen]|
| - Model Switcher    |   * Assistant Card                    |                                 |
| - System Health &   |     - Grounding Confidence Badge      | [Render Surface]                |
|   Index Statistics  |     - Router Rationale Pill           |  * Experiment Card UI           |
|                     |     - Rendered Markdown & Quotes      |  * Sandboxed HTML (CSP iframe)  |
|                     |     - [Open in Artifact Viewer]       |  * Ship 30 Rich Markdown Essay  |
|                     |                                       |                                 |
|                     | - Bottom Input Bar & Suggestions      |                                 |
+---------------------+---------------------------------------+---------------------------------+
```

---

## 3. Color Tokens & Visual Hierarchy

| Token Name | Hex Code | Purpose / Usage |
|---|---|---|
| **Canvas Background** | `#0b0f19` | Main application background |
| **Card Surface** | `#131b2e` | Assistant message containers, panels, modals |
| **Sidebar Background**| `#0d1424` | Session management and navigation bar |
| **Lenny Brand Primary**| `#ee771b` / `#df5c12` | Primary brand orange, user chat bubbles, active buttons |
| **Emerald (High Grounding)** | `#10b981` / `#064e3b` | High confidence badge (>= 72% grounding), ready states |
| **Amber (Medium Grounding)** | `#f59e0b` / `#78350f` | Medium confidence badge, hypothesis callout boxes |
| **Orange (Low Grounding)** | `#f97316` / `#7c2d12` | Low confidence badge, caution indicators |
| **Rose (Insufficient Refusal)** | `#f43f5e` / `#4c0519` | Insufficient Grounding banner, deletion triggers |
| **Border Slate** | `#334155` / `#1e293b` | Structural dividers and cards |

---

## 4. Key Interaction States

### 4.1 Empty / Welcoming State
- Displays large Lenny logo, tagline, and an explanatory onboarding summary.
- Presents 4 quick-start suggestion chips:
  1. *Grounded Q&A:* "What did Brian Balfour say about growth loops vs funnels?"
  2. *Ship 30 Essay:* "Write a Ship 30 for 30 essay on Superhuman finding product-market fit"
  3. *Growth Experiment Card:* "Turn Elena Verna's B2B PLG advice into a 1-week growth experiment"
  4. *Refusal Guardrail Test:* "How do I bake traditional sourdough bread at home?"

### 4.2 Grounding Confidence Badge States
Every assistant response renders a real-time badge at the top of the message:
- **High Grounding (Green):** Displays `ShieldCheck`, percentage match (e.g. `(88%)`), and an interactive `3 sources` pill opening the Citation Inspector.
- **Medium Grounding (Yellow):** Displays `AlertTriangle` warning of partial coverage.
- **Low Grounding (Orange):** Displays `ShieldAlert` advising user caution.
- **Insufficient Grounding / Refusal (Red Banner):** Visibly halts answer generation, shows `XCircle`, and presents an honest refusal explaining that Lenny's podcast does not cover the topic.

### 4.3 Citation & Transcript Inspector Drawer
Clicking any citation count pill triggers an overlay modal:
- Shows episode title, guest name, and exact percentage match.
- Highlights verbatim transcript quotes in a monospace quote box.
- Provides direct links to the YouTube episode.

### 4.4 Growth Experiment Card View
When Skill 3 executes, the Artifact Viewer mounts a structured card:
- **Hypothesis Banner:** Highlighted amber callout box enforcing `If [Action], then [Outcome], because [Mechanism]`.
- **Target Metric Box:** Large monospace font highlighting the single primary KPI.
- **Sprint Schedule Timeline:** Vertical step cards for `Day 1-2`, `Day 3-4`, and `Day 5-7`.
- **Risks & Invalidation Matrix:** Rose-bordered cautionary bullets.
- **Attribution Card:** Guest name, episode title, and transcript quote.

---

## 5. Sandboxing & Security Isolation Model

To guarantee 100% security against untrusted LLM-generated HTML and CSS:
1. **Iframe Sandboxing Attribute:**
   ```html
   <iframe sandbox="allow-scripts" srcdoc="..." />
   ```
   - Strictly **NO** `allow-same-origin`: Browser treats the iframe content as a unique opaque origin.
   - The iframe cannot access `window.parent`, `window.top`, `document.cookie`, `localStorage`, or `sessionStorage` of the host app.
   - Strictly **NO** `allow-top-navigation`: The iframe cannot hijack or redirect the parent application window.
2. **Content Security Policy (CSP):**
   Injected HTML contains a strict CSP header:
   ```html
   <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'unsafe-inline'; img-src data: https:;">
   ```
   - Prevents exfiltration of data via unauthorized `fetch` or `XMLHttpRequest`.
   - Allows safe styling and local rendering only.

---

## 6. Accessibility & Keyboard Ergonomics

- **Keyboard Navigation:**
  - `Enter` submits user query; `Shift + Enter` inserts multiline newline.
  - `Escape` closes the Citation Drawer or exits Artifact Fullscreen mode.
- **Screen Reader Support:** All icon buttons include explicit `title` and `aria-label` attributes.
- **Color Contrast:** All text tokens comply with WCAG 2.1 AA standards for contrast on dark backgrounds.
