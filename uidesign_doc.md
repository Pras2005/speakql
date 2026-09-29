# SpeakQL Enterprise — Frontend Design Specification v2

> **For AI agents executing this spec:**
> Read every section in full before writing a single line of code.
> Every value — color, size, font weight, border width, z-index — is a hard requirement unless the word `[OPTIONAL]` appears next to it.
> Do not substitute. Do not improve. Do not add features not listed here.
> When you are unsure: do less, not more. Ask before guessing.

---

## 0. Agent quick-start checklist

Complete every item before touching any component file.

- [ ] Read this entire document first
- [ ] Framework: React 18 + TypeScript + Vite
- [ ] Styling: `globals.css` for CSS variables + Tailwind CSS v3 for layout utilities only
- [ ] State: Zustand for UI/session state, TanStack Query v5 for server state
- [ ] Router: React Router v6 with nested routes
- [ ] Icons: `lucide-react` only — no heroicons, no fontawesome, nothing else
- [ ] Fonts: IBM Plex Mono (400, 500) + IBM Plex Sans (400, 500) via Google Fonts in `index.html`
- [ ] All colors come from CSS variables — zero hardcoded hex values in any `.tsx` file
- [ ] Theme is controlled by `data-theme="dark"` or `data-theme="light"` on `<html>` element
- [ ] No component file exceeds 200 lines — split ruthlessly
- [ ] Every component has a named TypeScript interface for its props directly above the component
- [ ] No `any` types anywhere
- [ ] Run `npx tsc --noEmit` — zero errors before calling done

---

## 1. Design philosophy

### What this is

SpeakQL is a **governed data workbench**, not a chat application.
The SQL editor and results table are the primary elements.
The natural language prompt is a secondary input — a fast way to generate a first draft.
The governance layer (policy, masking, audit, risk) is always visible, never hidden in a modal.

### Visual reference

Bloomberg Terminal + Reuters Eikon — but modern, not retro.
- Dense information without clutter
- Amber gold as the single brand accent
- Monospace typography throughout — this is a tool for people who read data
- Two themes (dark and light) that are equal citizens — not "dark mode as afterthought"
- No rounded pill buttons. No gradient cards. No chat bubbles. No animations except theme transition.

### What this is NOT

- Not a chat interface (no message bubbles, no conversation history taking up 50% of the screen)
- Not a dashboard (no pie charts, no KPI widgets on the landing page)
- Not a SaaS landing page (no hero sections, no feature cards)
- Not a mobile app (desktop only, minimum viewport 1280px)

---

## 2. Tech stack — exact versions

```json
{
  "react": "^18.3.0",
  "react-dom": "^18.3.0",
  "typescript": "^5.4.0",
  "vite": "^5.2.0",
  "tailwindcss": "^3.4.0",
  "postcss": "^8.4.0",
  "autoprefixer": "^10.4.0",
  "zustand": "^4.5.0",
  " @tanstack/react-query": "^5.28.0",
  "react-router-dom": "^6.22.0",
  "lucide-react": "^0.378.0",
  "axios": "^1.6.0"
}
```

Install sequence:

```bash
npm create vite@latest speakql-client -- --template react-ts
cd speakql-client
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install zustand @tanstack/react-query react-router-dom lucide-react axios
```

---

## 3. Project file structure — exact

Do not create files outside this structure without explicit instruction.

```
speakql-client/
├── index.html                        ← font imports live here
├── src/
│   ├── main.tsx                      ← Vite entry, providers, router
│   ├── App.tsx                       ← Route tree only, no logic
│   ├── globals.css                   ← ALL CSS variables, theme blocks, keyframes
│   │
│   ├── store/
│   │   ├── themeStore.ts             ← Zustand: 'dark' | 'light', toggle fn
│   │   ├── sessionStore.ts           ← Zustand: user, workspace, role, db
│   │   └── workbenchStore.ts         ← Zustand: prompt, sql, status, result
│   │
│   ├── api/
│   │   ├── client.ts                 ← Axios instance, auth interceptor
│   │   ├── agent.ts                  ← /api/v1/agent/* calls
│   │   ├── audit.ts                  ← /api/v1/audit/* calls
│   │   ├── catalog.ts                ← /api/v1/catalog/* calls
│   │   └── policy.ts                 ← /api/v1/policy/* calls
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Shell.tsx             ← Root layout: Topbar + Rail + Outlet
│   │   │   ├── Topbar.tsx            ← Logo, breadcrumb, nav tabs, theme toggle
│   │   │   └── Rail.tsx              ← Left icon rail (36px wide)
│   │   │
│   │   ├── workbench/
│   │   │   ├── SQLEditor.tsx         ← Syntax-highlighted SQL display + actions
│   │   │   ├── ContextPanel.tsx      ← Session, risk, explain, audit trail
│   │   │   ├── ResultsPanel.tsx      ← Results table spanning full width
│   │   │   ├── PromptBar.tsx         ← Bottom NL input bar
│   │   │   ├── RiskBar.tsx           ← Risk score visualisation (used in ContextPanel)
│   │   │   └── ApprovalBanner.tsx    ← Shown instead of results on deny/pending
│   │   │
│   │   ├── audit/
│   │   │   └── AuditTable.tsx
│   │   │
│   │   ├── catalog/
│   │   │   └── CatalogCard.tsx
│   │   │
│   │   ├── policy/
│   │   │   └── PolicyRuleCard.tsx
│   │   │
│   │   └── shared/
│   │       ├── PanelHeader.tsx       ← Reusable panel header bar (title + tags + actions)
│   │       ├── Tag.tsx               ← Coloured tag/badge component
│   │       └── SectionLabel.tsx      ← Uppercase mono section label
│   │
│   ├── views/
│   │   ├── WorkbenchView.tsx         ← Main 2×2 grid layout
│   │   ├── AuditView.tsx
│   │   ├── CatalogView.tsx
│   │   └── PolicyView.tsx
│   │
│   └── data/
│       ├── mockWorkbench.ts          ← Mock SQL, results, context
│       ├── mockAudit.ts              ← Mock audit events
│       ├── mockCatalog.ts            ← Mock catalog entries
│       └── mockPolicy.ts             ← Mock policy rules
```

---

## 4. Font setup — `index.html`

Replace the `<head>` section of `index.html` with exactly this:

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SpeakQL</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

Note: `data-theme="dark"` is on `<html>`. This is where all theme CSS variable blocks are scoped.

---

## 5. CSS variables — `src/globals.css`

This is the complete file. Do not add to it. Do not remove from it.
Every color in every component must reference one of these variables.

```css
 @tailwind base;
 @tailwind components;
 @tailwind utilities;

 @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Sans:wght@400;500&display=swap');

/* ─── DARK THEME ─────────────────────────────────────── */
html[data-theme="dark"] {

  /* Backgrounds — 5 levels of depth */
  --bg0: #0C0C0A;   /* page / outermost */
  --bg1: #111110;   /* topbar, rail, panel headers */
  --bg2: #171715;   /* panel bodies */
  --bg3: #1E1E1B;   /* hover states, inset areas */
  --bg4: #252522;   /* active states, deepest inset */

  /* Borders */
  --bd:  rgba(255, 255, 255, 0.07);   /* default dividers */
  --bd2: rgba(255, 255, 255, 0.12);   /* card edges, input borders */
  --bd3: rgba(255, 255, 255, 0.20);   /* focused inputs */

  /* Text */
  --t1: #F0EDE6;   /* primary readable text */
  --t2: #9A9690;   /* secondary — labels, meta */
  --t3: #5A5750;   /* tertiary — hints, line numbers */
  --t4: #2E2E2A;   /* quaternary — very dim, ranks */

  /* Brand accent — amber gold */
  --amber:    #C8A84B;
  --amber-bg: rgba(200, 168, 75, 0.12);
  --amber-bd: rgba(200, 168, 75, 0.28);
  --amber-t:  #C8A84B;   /* amber text on dark bg */

  /* Semantic — red (deny, error, critical) */
  --red:    #C8503C;
  --red-bg: rgba(200, 80,  60,  0.12);
  --red-bd: rgba(200, 80,  60,  0.28);
  --red-t:  #C8503C;

  /* Semantic — green (allow, success, low risk) */
  --green:    #5CA870;
  --green-bg: rgba(92,  168, 112, 0.12);
  --green-bd: rgba(92,  168, 112, 0.28);
  --green-t:  #5CA870;

  /* Semantic — blue (info, table names) */
  --blue:    #4A80C0;
  --blue-bg: rgba(74,  128, 192, 0.12);
  --blue-bd: rgba(74,  128, 192, 0.28);
  --blue-t:  #4A80C0;

  /* Semantic — purple (masked, PII) */
  --purple:    #9A60C8;
  --purple-bg: rgba(154, 96,  200, 0.12);
  --purple-bd: rgba(154, 96,  200, 0.28);
  --purple-t:  #9A60C8;

  /* SQL syntax highlighting */
  --sql-keyword:  #C8503C;   /* SELECT, FROM, WHERE, JOIN... */
  --sql-table:    #4A80C0;   /* table names */
  --sql-string:   #5CA870;   /* 'string literals' */
  --sql-function: #9A60C8;   /* SUM(), COUNT()... */
  --sql-linenum:  #2E2E2A;   /* line number gutter */

  /* Layout */
  --topbar-h:  38px;
  --rail-w:    36px;
  --prompt-h:  46px;
}

/* ─── LIGHT THEME ────────────────────────────────────── */
html[data-theme="light"] {

  --bg0: #F5F2EC;
  --bg1: #EDE9E0;
  --bg2: #FDFAF5;
  --bg3: #F0EDE5;
  --bg4: #E8E4DA;

  --bd:  rgba(0, 0, 0, 0.09);
  --bd2: rgba(0, 0, 0, 0.16);
  --bd3: rgba(0, 0, 0, 0.28);

  --t1: #1A1A16;
  --t2: #6A6660;
  --t3: #A0998F;
  --t4: #C8C4BC;

  --amber:    #8A6A10;
  --amber-bg: rgba(138, 106, 16,  0.10);
  --amber-bd: rgba(138, 106, 16,  0.30);
  --amber-t:  #8A6A10;

  --red:    #8A3020;
  --red-bg: rgba(138, 48,  32,  0.08);
  --red-bd: rgba(138, 48,  32,  0.25);
  --red-t:  #8A3020;

  --green:    #2A6B3A;
  --green-bg: rgba(42,  107, 58,  0.08);
  --green-bd: rgba(42,  107, 58,  0.25);
  --green-t:  #2A6B3A;

  --blue:    #1A4A7A;
  --blue-bg: rgba(26,  74,  122, 0.08);
  --blue-bd: rgba(26,  74,  122, 0.25);
  --blue-t:  #1A4A7A;

  --purple:    #5A2A8A;
  --purple-bg: rgba(90,  42,  138, 0.08);
  --purple-bd: rgba(90,  42,  138, 0.25);
  --purple-t:  #5A2A8A;

  --sql-keyword:  #8A3020;
  --sql-table:    #1A4A7A;
  --sql-string:   #2A6B3A;
  --sql-function: #5A2A8A;
  --sql-linenum:  #C8C4BC;

  --topbar-h:  38px;
  --rail-w:    36px;
  --prompt-h:  46px;
}

/* ─── GLOBAL RESETS ──────────────────────────────────── */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #root {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  background: var(--bg0);
  color: var(--t1);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Theme transition — smooth but not slow */
html {
  transition: background 0.18s ease, color 0.18s ease;
}

/* ─── SCROLLBARS ─────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bd2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--bd3); }

/* ─── KEYFRAMES ──────────────────────────────────────── */
 @keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

---

## 6. Tailwind config — `tailwind.config.js`

Replace the file with exactly this:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['IBM Plex Mono', 'monospace'],
        sans: ['IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

Note: Do not extend colors in Tailwind config. All colors live in CSS variables in `globals.css`. Use inline styles like `style={{ color: 'var(--amber)' }}` or create small wrapper components for semantic colors.

---

## 7. Typography rules — complete reference

Every text element in the app must match one of these exactly.

| Role | Font family | Size | Weight | Color variable | Notes |
|---|---|---|---|---|---|
| Logo | `IBM Plex Mono` | 13px | 500 | `--t1` | `SPEAK` in `--t1`, `QL` in `--amber` |
| Breadcrumb | `IBM Plex Mono` | 10px | 400 | `--t3` → `--t2` → `--amber` | Dimmer → brighter → active |
| Nav tab default | `IBM Plex Mono` | 10px | 400 | `--t3` | uppercase, tracking 0.07em |
| Nav tab active | `IBM Plex Mono` | 10px | 400 | `--amber` | + 2px bottom border `--amber` |
| Panel title | `IBM Plex Mono` | 9px | 500 | `--t3` | uppercase, tracking 0.10em |
| Section label | `IBM Plex Mono` | 9px | 500 | `--t3` | uppercase, tracking 0.08em |
| Body / cell text | `IBM Plex Mono` | 11px | 400 | `--t1` | |
| Muted / meta | `IBM Plex Mono` | 10px | 400 | `--t2` | |
| Hint / dim | `IBM Plex Mono` | 9px | 400 | `--t3` | |
| Line numbers | `IBM Plex Mono` | 10px | 400 | `--sql-linenum` | |
| SQL keywords | `IBM Plex Mono` | 11px | 500 | `--sql-keyword` | |
| SQL table names | `IBM Plex Mono` | 11px | 400 | `--sql-table` | |
| SQL strings | `IBM Plex Mono` | 11px | 400 | `--sql-string` | |
| SQL functions | `IBM Plex Mono` | 11px | 400 | `--sql-function` | |
| Table header | `IBM Plex Mono` | 9px | 500 | `--t3` | uppercase, tracking 0.08em |
| Table cell | `IBM Plex Mono` | 10px | 400 | `--t1` | |
| Numeric cell | `IBM Plex Mono` | 10px | 500 | `--blue-t` | right-aligned |
| Masked cell | `IBM Plex Mono` | 10px | 400 | `--t3` | italic, content: `[ masked · PII ]` |
| Tag label | `IBM Plex Mono` | 9px | 400 | semantic | see Tag component |
| Prompt input | `IBM Plex Mono` | 11px | 400 | `--t1` | placeholder: `--t4` |
| Button label | `IBM Plex Mono` | 10px | 500 | semantic | uppercase, tracking 0.06em |

Rules:
- Never use font-weight 600 or 700
- Never use font size below 9px
- IBM Plex Sans is used only in the prompt input placeholder and explain text — everywhere else is Mono
- Never mix fonts within a single UI element

---

## 8. Layout — shell and grid

### 8.1 Overall shell

The app occupies 100vw × 100vh with no scroll at the shell level.

```
┌──────────────────────────────── 100vw ─────────────────────────────────┐
│  TOPBAR                                                      height: 38px│
├──────┬─────────────────────────────────────────────────────────────────┤
│ RAIL │  VIEW OUTLET (renders WorkbenchView, AuditView, etc.)           │
│ 36px │  height: calc(100vh - 38px)                                     │
│      │  overflow: hidden (each view manages its own scroll)            │
└──────┴─────────────────────────────────────────────────────────────────┘
```

### 8.2 WorkbenchView grid

The workbench is a 2×2 grid. Top row: SQL editor (left) + Context panel (right). Bottom row: Results panel spanning both columns.

```
┌─────────────────────────┬──────────────────────────┐
│  SQL EDITOR             │  CONTEXT PANEL           │
│  flex: 1                │  width: 340px            │
│  min-height: 260px      │  min-height: 260px       │
├─────────────────────────┴──────────────────────────┤
│  RESULTS PANEL                                     │
│  width: 100%                                       │
│  flex: 1 (takes remaining height)                  │
├────────────────────────────────────────────────────┤
│  PROMPT BAR                                height: 46px│
└────────────────────────────────────────────────────┘
```

### 8.3 Panel anatomy

Every panel (SQL editor, Context, Results) follows this structure:

```
┌─ PanelHeader (30px tall) ──────────────────────────────────┐
│  [PANEL TITLE]  [tag] [tag]  ·····  [action] [action]      │
│  bg: --bg1, border-bottom: 0.5px solid --bd                │
├────────────────────────────────────────────────────────────┤
│  Panel body                                                │
│  bg: --bg2                                                 │
│  overflow-y: auto (each panel scrolls independently)       │
└────────────────────────────────────────────────────────────┘
```

---

## 9. Component specifications

### 9.1 Topbar

Height: `var(--topbar-h)` = 38px. Background: `var(--bg1)`. Border-bottom: `0.5px solid var(--bd)`.

**Center zone — navigation tabs:**
Tabs (in order): `WORKBENCH` · `AUDIT VAULT` · `CATALOG` · `POLICY` · `APPROVALS`

### 9.2 Rail (left icon strip)

Width: `var(--rail-w)` = 36px. Background: `var(--bg1)`. Border-right: `0.5px solid var(--bd)`.

### 9.3 PanelHeader (shared component)

Height: 30px. Background: `var(--bg1)`. Border-bottom: `0.5px solid var(--bd)`.

### 9.4 Tag (shared component)

Variants: `amber` | `green` | `red` | `blue` | `purple` | `neutral`

### 9.5 SQLEditor

SQL syntax highlighting for keywords, table names, strings, and functions.

### 9.6 ContextPanel

Width: 340px (fixed). Sections: SESSION, RISK ANALYSIS, WHY THIS SQL, AUDIT TRAIL.

### 9.7 ResultsPanel

Table spanning full width. Features masked column rendering and export actions.

### 9.8 ApprovalBanner

Shown on deny/pending. Styled according to risk level.

### 9.9 PromptBar

Height: 46px. NL input bar with blinking cursor and keyboard hints.

---

## 10. State management

Stores for `theme`, `session`, and `workbench` state using Zustand.

---

## 11. API layer

Axios client with interceptors for auth. Endpoints for `agent`, `audit`, `catalog`, and `policy`.

---

## 12. Routing

React Router with `Shell` layout and nested routes for `workbench`, `audit`, `catalog`, and `policy`.

---

## 13. Mock data

Mock data provided for v1 implementation.

---

## 14. Other views

Specifications for `AuditView`, `CatalogView`, and `PolicyView`.

---

## 15. Loading and error states

Consistent loading (blinking dots) and error display across all panels.

---

## 16. What NOT to build in v1

Login screens, responsive layout, real API calls (v1 uses mocks), complex animations.

---

## 17. Definition of done — v1

- All views render correctly.
- Theme toggle works.
- Syntax highlighting works.
- No TypeScript or console errors.
- Visuals match specification exactly.

---

## 18. Environment setup

`.env.local` and `.env.example` configurations.

---

*SpeakQL Enterprise UI Design Specification v2 — Bloomberg/Reuters dual-theme workbench edition.*
*Every value in this document is intentional. Execute it literally.*
