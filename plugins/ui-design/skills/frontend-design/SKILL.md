---
name: frontend-design
description: "Builds or refactors multi-file frontend projects — HTML/CSS, React, Vue, or any stack — following the Indicium AI visual identity and clean code principles. Output is always a structured, maintainable codebase with separated concerns (tokens, base, layout, components). CALL THIS TOOL IMMEDIATELY — without waiting for project details — whenever: the user mentions 'frontend-design' by name; says 'use the frontend-design skill' or 'run the frontend-design skill'; asks to apply Indicium branding, refactor the visual design, update CSS to Indicium standard, redesign or rebrand a web app, build a new web app or frontend, or create a new web page with Indicium style. The skill handles all interactive information gathering itself. Do NOT use this skill for: standalone single-file HTML outputs meant to be shared or presented (use html-deck-creator instead); slide decks, dashboards, or reports that live in one file; one-shot visual artifacts that will not be maintained as a codebase."
triggers:
  - "frontend-design"
  - "use the frontend-design skill"
  - "apply Indicium branding to"
  - "rebrand the web app"
  - "refactor the UI to Indicium style"
  - "apply Indicium branding"
  - "refactor the visual design"
  - "apply Indicium design"
  - "redesign the app"
  - "update CSS to Indicium standard"
  - "build a web app with Indicium"
  - "create a frontend with Indicium style"
  - "create a new web page with Indicium"
---

# Frontend Design

Builds new frontend projects or refactors existing ones to comply with the Indicium AI visual
identity. Works across stacks — plain HTML/CSS, React, Vue, or any component-based frontend.

## Not this skill when

Use the **`html-deck-creator`** skill instead if the user wants:

- A **standalone single-file HTML artifact** — dashboard, slide deck, guide, or report — meant to be shared or opened directly in a browser
- A **presentation or visual summary** of data or project results (OKR tracker, KPI dashboard, keynote deck)
- Any output that will **not be maintained as a codebase** — something delivered as a file, not committed to a repo

The clearest signal: if the output will live in a repo and be maintained by developers → `frontend-design`. If it will be opened in a browser as a finished product and shared as a file → `html-deck-creator`.

---

**Two modes of operation:**
- **New project** — scaffolds a well-structured frontend from scratch, applying the brand system
  from the first line of code.
- **Existing project** — audits the current codebase and applies branding, layout restructuring,
  or a full visual overhaul depending on the requested scope.

**Core principle:** every file produced or modified must be more maintainable than what it
replaces. Concerns are always separated across files; raw values are never scattered across the
codebase; structure is always predictable to a developer opening the project for the first time.

---

## Step 1 — Load the brand guide

Read `brand/indicium_ai.md` using the Read tool.

This is the **non-negotiable design authority**: palette, typography, spacing, logo rules, and
copy tone. Every decision made in subsequent steps must be reconcilable with it.

---

## Step 2 — Determine the mode

Ask the user using `AskUserQuestion`:
- **question:** "Are you starting a new project or working on an existing one?"
- **options:**
  - `"New project — build from scratch"`
  - `"Existing project — refactor / rebrand"`

Record the answer as `MODE`: `new` or `existing`.

---

## If MODE = `new` → follow Steps 3A–5A, then jump to Step 6

## If MODE = `existing` → follow Steps 3B–5B, then continue to Step 6

---

## Step 3A — Gather requirements (new project)

Ask the user (free text): **"Describe the project: what is it for, what pages or views does it
need, what kind of content or data will it show, and which tech stack do you prefer?"**

Collect and record:
- **Purpose** — what the app does
- **Pages / views** — list of screens (e.g. landing, dashboard, settings)
- **Key components** — navbar, sidebar, cards, tables, forms, modals
- **Stack** — plain HTML/CSS, React, Vue, or other
- **Any constraints** — must integrate with an existing backend, specific browser support, etc.

If the user already described the project earlier in the conversation, extract this information
from context and skip the question.

---

## Step 4A — Propose the file structure (new project)

Based on the requirements and chosen stack, propose a file structure before writing any code.
Use the baseline below and adapt it to the stack:

**Plain HTML/CSS baseline:**
```
<project-root>/
├── index.html
├── css/
│   ├── tokens.css        ← brand design tokens (:root variables)
│   ├── base.css          ← reset, body, typography defaults
│   ├── layout.css        ← page-level grid and structural rules
│   ├── components/
│   │   ├── navbar.css
│   │   ├── button.css
│   │   └── card.css
│   └── main.css          ← @imports only, no rules of its own
├── js/
│   ├── main.js           ← app entry point, no DOM styling
│   └── components/
│       └── [name].js     ← behavior only, no inline style manipulation
└── assets/
    └── [logo files]
```

**React baseline:** `src/styles/tokens.css` + `globals.css` + `ComponentName.module.css` per component.
**Vue baseline:** `assets/tokens.css` + `assets/base.css` + `<style scoped>` per component.

Present the proposed structure and ask for confirmation using `AskUserQuestion`:
- **question:** "Does this structure work for you?"
- **options:** `["Yes, go ahead", "I want to adjust it first"]`

Collect feedback and revise until confirmed.

---

## Step 5A — Build the project (new project)

Generate all files according to the confirmed structure. Apply the brand guide and code quality
rules from Step 6 from the very first file. Then skip to Step 7.

---

## Step 3B — Understand the scope (existing project)

Ask the user using `AskUserQuestion`:
- **question:** "What do you want to do with the existing project?"
- **options:**
  - `"Apply branding only (colors, fonts, spacing) without changing the layout"`
  - `"Refactor layout and apply branding"`
  - `"Full redesign (layout + visual + component structure)"`

Record the answer as `SCOPE`: `branding`, `layout`, or `redesign`.

---

## Step 4B — Locate and audit the project (existing project)

If the user already provided a path earlier in the conversation, use it. Otherwise ask
(free text): **"What is the path to the project? It can be relative to the current directory
or absolute."**

Once you have the path, use Glob and the Read tool to map the project:

1. List all files recursively — look for `.html`, `.css`, `.js`, `.jsx`, `.tsx`, `.vue`, `.ts`
2. Identify the **tech stack** from file extensions and (if present) `package.json`
3. Identify the **entry point** — typically `index.html`, `App.jsx`, `App.vue`, or `main.ts`
4. Identify the **styling approach** — global CSS, CSS modules, Tailwind, styled-components, etc.
5. Identify **maintainability issues**: inline styles, raw hex values scattered across files,
   monolithic CSS files, JavaScript mixing styling logic with behavior

Read the key styling files. Look for:
- Current color values (hex, rgb, CSS variables)
- Current font families and sizes
- Current spacing values (padding, margin, gap)
- Layout structure (flexbox, grid, fixed widths)
- What conflicts with the brand guide and what can be preserved

---

## Step 5B — Present an action plan (existing project)

Before touching any file, present the user with a clear plan:

```
## Proposed changes

### File structure after refactor
<project-root>/
├── index.html               ← markup only, no inline styles or <style> blocks
├── css/
│   ├── tokens.css           ← brand design tokens (:root variables)
│   ├── base.css             ← reset, body, typography defaults
│   ├── layout.css           ← page-level grid and structural rules
│   ├── components/
│   │   ├── navbar.css
│   │   ├── button.css
│   │   └── card.css
│   └── main.css             ← @imports only
└── js/
    ├── main.js
    └── components/
        └── [component].js

### Files to create / modify
- `css/tokens.css`  — new file with all brand CSS variables
- `css/base.css`    — new file with reset and typography base
- `path/to/old.css` — split into component files listed above
- `index.html`      — remove inline styles, link to new CSS structure

### Design decisions
- Colors: #xxx → var(--vibrant-blue), #yyy → var(--dark-blue), …
- Fonts: adding Inter + Roboto Mono via Google Fonts
- Spacing: aligning all values to 8px rhythm

### Layout changes  ← only if SCOPE = layout or redesign
- [Describe structural changes proposed]

### What will NOT change
- Business logic, event handlers, data fetching — untouched
- [Any visual elements worth preserving]
```

Adapt the proposed structure to the actual stack found during the audit.

Ask for confirmation using `AskUserQuestion` before proceeding:
- **question:** "Can I proceed with these changes?"
- **options:** `["Yes, go ahead", "I want to adjust the plan first"]`

Collect feedback and revise until confirmed.

---

## Step 6 — Generate / apply the code

For **new projects**: use the Write tool to create each file in the confirmed structure.
For **existing projects**: use the Edit tool to modify existing files; use Write only for new
files. Never use Write on an existing file — it overwrites content outside the visual scope.

### Code quality rules — always apply regardless of mode

**Separation of concerns — non-negotiable:**
- HTML files contain only semantic markup. No `<style>` blocks. No inline `style=""` attributes.
- CSS files contain only visual rules. No JavaScript. No business logic.
- JavaScript files manipulate behavior and state only. Never set `.style.color`, `.style.padding`,
  or any inline style directly — use CSS class toggling instead.

**No raw values in component files:**
- All colors, font sizes, spacing, border-radius, and shadow values must reference a CSS variable
  defined in `tokens.css` (or the stack equivalent). Raw hex values like `#3a58ee` must not
  appear outside the token file.

**One responsibility per CSS file:**
- `tokens.css` — design tokens only (`--variable: value`)
- `base.css` — reset, `body`, `html`, heading defaults, link defaults
- `layout.css` — page-level structural rules (grid, sidebar, main content width)
- `components/<name>.css` — styles scoped to a single UI component
- `main.css` — `@import` statements only, no rules of its own

**Predictable import order in `main.css`:**
```css
@import './tokens.css';
@import './base.css';
@import './layout.css';
@import './components/navbar.css';
@import './components/button.css';
/* … other components … */
```

**Naming convention — BEM for plain CSS:**
```css
/* Block */    .card { }
/* Element */  .card__title { }
/* Modifier */ .card--featured { }
```
For React/Vue with CSS modules or scoped styles, component-local naming is acceptable.

---

### Brand guide application rules

**Design tokens — define once in `tokens.css` (or stack equivalent):**

```css
:root {
  /* Brand colors */
  --dark-blue:     #1c1d2f;
  --white:         #ffffff;
  --vibrant-blue:  #3a58ee;
  --atlantic-blue: #699bfb;
  --lavender:      #dedaf4;
  --teal:          #aae2e5;

  /* Semantic aliases — use these in components, not raw brand names */
  --color-bg:          var(--dark-blue);
  --color-bg-surface:  #f5f6fb;
  --color-bg-subtle:   #eef0f8;
  --color-text:        #0d0e1c;
  --color-text-muted:  #3d3f5c;
  --color-text-faint:  #7b7e9e;
  --color-border:      #e2e4f0;
  --color-accent:      var(--vibrant-blue);
  --color-accent-soft: rgba(58, 88, 238, 0.1);

  /* Spacing scale (0.5rem grid — rem so values scale with browser font-size) */
  --space-1: 0.25rem;   /* 4px  */
  --space-2: 0.5rem;    /* 8px  */
  --space-3: 1rem;      /* 16px */
  --space-4: 1.5rem;    /* 24px */
  --space-5: 2rem;      /* 32px */
  --space-6: 3rem;      /* 48px */
  --space-7: 4rem;      /* 64px */

  /* Fluid spacing — use for section padding and gaps that must breathe on small screens */
  --space-fluid-sm: clamp(var(--space-2), 2vw, var(--space-3));
  --space-fluid-md: clamp(var(--space-3), 4vw, var(--space-5));
  --space-fluid-lg: clamp(var(--space-4), 6vw, var(--space-6));

  /* Typography */
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'Roboto Mono', monospace;
  /* Static sizes (rem) — scale with browser font-size preference */
  --font-size-xs:   0.625rem;  /* 10px */
  --font-size-sm:   0.75rem;   /* 12px */
  --font-size-base: 0.875rem;  /* 14px */
  --font-size-md:   1rem;      /* 16px */
  /* Fluid sizes (clamp) — grow smoothly from mobile to wide desktop */
  --font-size-lg:  clamp(1.25rem, 2vw + 0.5rem, 1.5rem);    /* 20–24px */
  --font-size-xl:  clamp(1.5rem,  3vw + 0.75rem, 2.25rem);  /* 24–36px */
  --font-size-2xl: clamp(2rem,    5vw + 1rem, 3.75rem);      /* 32–60px */

  /* Radii (rem for proportional scaling) */
  --radius-sm:   0.375rem;  /* 6px  */
  --radius:      0.75rem;   /* 12px */
  --radius-lg:   1.25rem;   /* 20px */
  --radius-full: 624.9375rem; /* pill — always circular */

  /* Shadows */
  --shadow-sm: 0 1px 4px rgba(58, 88, 238, 0.06);
  --shadow:    0 2px 12px rgba(58, 88, 238, 0.10);

  /* Transitions */
  --ease:     cubic-bezier(0.4, 0, 0.2, 1);
  --duration: 200ms;
}
```

**Typography** — define in `base.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Roboto+Mono:wght@400;500;700&display=swap');

/* 16px anchor — rem values in tokens.css are relative to this */
html { font-size: 100%; }
body { font-family: var(--font-sans); color: var(--color-text); line-height: 1.5; }
code, kbd, pre, .label, .chip, .badge { font-family: var(--font-mono); }
```

Roboto Mono applies **only** to buttons, chips, labels, badges, and code — never to body copy.

**Spacing** — always use `--space-*` variables. Never write `padding: 13px` or `gap: 20px`.
For section-level padding and gaps that must adapt to the viewport, prefer `--space-fluid-*` variables.

**Logo** — use the correct asset for each background context:

| Background | Recommended asset | Notes |
|------------|------------------|-------|
| Dark (`--dark-blue` or any dark surface) | `assets/IndiciumAI_logo_white.png` | Full-color white wordmark |
| Dark — monochrome only | `assets/IndiciumAI_logo_mono_white.png` | Single-color white wordmark |
| Light / white surface | `assets/IndiciumAI_logo_black.png` | Full-color black wordmark |
| Light — monochrome only | `assets/IndiciumAI_logo_mono_black.png` | Single-color black wordmark |
| Brand blue surface (`--vibrant-blue`) | `assets/IndiciumAI_logo_dark_blue.png` | Dark blue wordmark on blue backgrounds |
| Neutral / mid-tone surface | `assets/IndiciumAI_logo_blue.png` | Vibrant-blue wordmark on neutral backgrounds |
| Favicon / compact / icon-only | `assets/IndiciumAI_icon.svg` | Vector icon, no wordmark |
| Hero / background decoration | `assets/background.gif` | Animated brand background — decorative use only |

Copy the required files from `assets/` (sibling of this SKILL.md) into the target project's
static assets folder. Adjust `<img src="">` or CSS `url()` paths accordingly.

**Interactions** — apply consistently via `base.css`:

```css
a, button, [role="button"] {
  transition: all var(--duration) var(--ease);
}
```

### Layout rules — apply when SCOPE = `layout` or `redesign`, or for all new projects

- CSS Grid for page-level layout (sidebar + main, header + content + footer)
- Flexbox for component-level alignment (navbar items, card rows, button groups)
- Layout rules live exclusively in `layout.css` — not in component files
- Maximum content width: `min(80rem, 100% - var(--space-fluid-md) * 2)` centered via `margin-inline: auto`
- Responsive breakpoints use `em` (scales with browser zoom, safer than `px`):
  - `48em` (tablet — 768px equivalent)
  - `64em` (desktop — 1024px equivalent)
  - `80em` (wide — 1280px equivalent)

```css
/* Example breakpoint pattern in layout.css */
@media (min-width: 48em) { /* tablet */ }
@media (min-width: 64em) { /* desktop */ }
@media (min-width: 80em) { /* wide */ }
```

### Stack-specific file conventions

| Stack | Token file | Base/global styles | Component styles |
|-------|-----------|-------------------|-----------------|
| Plain HTML/CSS | `css/tokens.css` | `css/base.css` | `css/components/<name>.css` |
| React (CSS modules) | `styles/tokens.css` | `styles/globals.css` | `ComponentName.module.css` |
| React (Tailwind) | `tailwind.config.js` → `theme.extend` | `styles/globals.css` | Utility classes in JSX |
| Vue | `assets/tokens.css` | `assets/base.css` | `<style scoped>` per component |
| Styled-components | `theme.ts` → `ThemeProvider` | `GlobalStyle` component | `styled.X` per component |

---

## Step 7 — Quality check

Verify both the visual result and the code structure:

**Visual (brand guide):**
- [ ] All colors reference `--variable` names — no raw hex values outside `tokens.css`
- [ ] Inter is the default body font; Roboto Mono is limited to accent/code elements
- [ ] All spacing uses `--space-*` or `--space-fluid-*` variables — no arbitrary pixel values
- [ ] Logo: correct asset file for each background context
- [ ] Hover/focus states: smooth `var(--duration) var(--ease)` transitions everywhere
- [ ] Type hierarchy is visually clear: heading → subheading → body → caption
- [ ] Fluid type (`--font-size-lg/xl/2xl`) scales smoothly — verify at 375px, 768px, and 1280px viewport widths

**Code quality (maintainability):**
- [ ] No inline `style=""` attributes in HTML or JSX
- [ ] No `<style>` blocks inside HTML files
- [ ] No raw hex values, font names, or spacing numbers outside `tokens.css`
- [ ] No raw `px` values in spacing, font-size, or media queries — use `rem`/`em`/`clamp()` instead
- [ ] Media queries use `em` units (e.g. `48em`, `64em`, `80em`), not `px`
- [ ] Each CSS file has a single, clearly scoped responsibility
- [ ] `main.css` (or equivalent) contains only `@import` statements
- [ ] No JavaScript sets inline styles — behavior uses CSS class toggling only
- [ ] For existing projects: no business logic, routing, or data-fetching code was modified
- [ ] Layout is responsive at `48em` (tablet), `64em` (desktop), and `80em` (wide)

If any item fails, fix it before reporting completion.

---

## Step 8 — Report

```
## Summary

### Mode
New project | Existing project refactor

### File structure
<tree of created/modified files>

### Design tokens defined
- [list of CSS variables in tokens.css]

### Files split or reorganized  ← existing projects only
- `old/monolithic.css` → tokens.css, base.css, components/…

### Layout changes (if any)
- [describe structural changes]

### Maintainability improvements  ← existing projects only
- [inline styles removed, concerns separated, etc.]

### Preserved  ← existing projects only
- [what was intentionally left untouched]
```
