# Indicium AI — Brand Guidelines

Reference document for AI systems generating UI designs, dashboards, presentations, and any visual artifact under the Indicium AI identity.

---

## Brand Identity at a Glance

| Attribute | Value |
|-----------|-------|
| **Tagline** | Enterprise AI, Delivered |
| **Mission** | Unlock value from Data & AI for enterprises with unmatched clarity, speed, and capability. |
| **Brand voice** | Confident, bold, direct, outcome-driven, conversational, technically credible |
| **Core audience** | C-Suite (CIO, CDO, CTO) and technical leaders at large enterprises |

---

## Values

| Value | Behavior |
|-------|----------|
| **Quality First** | Creative, respectful, challenging, ambitious, pragmatic — do it right or not at all. |
| **Stronger Together** | Collaborative, supportive, ambitious, driven — best solutions come from teamwork. |
| **Taking Ownership** | Accountable, empowered, passionate, proactive — always see things through. |
| **Delivering Value** | Customer-obsessed, innovative, adaptable — success means client outcomes. |

---

## Typography

### Typefaces

| Role | Family | Usage rule |
|------|--------|-----------|
| **Primary** | [Inter](https://fonts.google.com/specimen/Inter) | Headlines, page titles, subtitles, and all body copy |
| **Accent** | [Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono) | Buttons, chips, short labels, code snippets — never for long copy |

> **Rule:** Roboto Mono is an accent only. Never use it for paragraphs or sections set primarily in Inter.

### Type Scale

| Level | Font | Weight | Size |
|-------|------|--------|------|
| Document title | Inter | Medium | 60px |
| Page title | Inter | Normal | 24px |
| Subtitle | Inter | Normal | varies |
| Body text | Inter | Normal | 12px |
| Caption / small | Inter | Normal | 10px |
| Accent label | Roboto Mono | Normal | 12px or 10px |
| Accent label (boxed) | Roboto Mono | Normal | 12px or 10px |

---

## Color Palette

### Primary Colors

| Name | Hex | Role |
|------|-----|------|
| **Dark Blue** | `#1c1d2f` | Primary background, dark surfaces |
| **White** | `#ffffff` | Primary text on dark, light backgrounds |

### Accent Colors

| Name | Hex | Role |
|------|-----|------|
| **Vibrant Blue** | `#3a58ee` | Key emphasis, primary calls to action |
| **Atlantic Blue** | `#699bfb` | Illustrations, diagrams, secondary data points — use sparingly |
| **Lavender** | `#dedaf4` | Secondary CTAs, grid brand device, subtle fills |
| **Teal / Atlantic** | `#aae2e5` | Decorative accents in illustrations — use sparingly |

### Hierarchy Rules

- **Dark Blue + White** → structure and information (backgrounds, large text areas)
- **Vibrant Blue** → moments of emphasis and primary CTAs
- **Lavender** → secondary CTAs and the grid/brand device
- **Atlantic Blue** → illustrations and diagrams only (not UI chrome)
- **Vibrant Purple** → icons only (use sparingly)

### CSS Variables (recommended `:root` block)

```css
:root {
  --dark-blue:    #1c1d2f;
  --white:        #ffffff;
  --vibrant-blue: #3a58ee;
  --atlantic-blue:#699bfb;
  --lavender:     #dedaf4;
  --teal:         #aae2e5;

  /* Spacing rhythm */
  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  32px;
  --space-2xl: 48px;
}
```

---

## Logo

### Assets available

| File | Usage |
|------|-------|
| `../assets/IndiciumAI_logo_blue.png` | Default color logo (blue wordmark) — use on white/off-white backgrounds |
| `../assets/IndiciumAI_logo_dark_blue.png` | Dark blue color logo — use on light or neutral backgrounds |
| `../assets/IndiciumAI_logo_white.png` | Full-color white wordmark — use on dark or colored backgrounds |
| `../assets/IndiciumAI_logo_black.png` | Full-color black wordmark — high-contrast or print contexts |
| `../assets/IndiciumAI_logo_mono_white.png` | Monochrome white — use on dark or colored backgrounds |
| `../assets/IndiciumAI_logo_mono_black.png` | Monochrome black — high-contrast print contexts |
| `../assets/IndiciumAI_icon.svg` | Standalone icon — favicons, avatars, compact headers |
| `../assets/background.gif` | Animated brand background — use in hero sections, cover slides, and full-bleed decorative areas |

### Logo rules

- The **wordmark must never appear without the icon**.
- The icon **can** be used alone at very small sizes (favicon, avatar).
- Maintain **clear space** equal to the icon element's height on all sides — no text, imagery, or UI elements inside this zone.
- Preferred version on dark backgrounds: **white logo**.
- Preferred version on light backgrounds: **color logo or monochrome black**.

### Logo don'ts

- Do not recreate the wordmark in another typeface.
- Do not restyle the "AI" portion separately.
- Do not rotate, add shadows, outlines, or effects.
- Do not alter the icon in any way.
- Do not use unapproved lock-ups.

---

## Brand Voice & Tone

### Principles

| Principle | Description |
|-----------|-------------|
| **Confident and direct** | Punchy, precise — avoid weak phrasing or unnecessary words. |
| **Outcome-driven** | Every message ties back to measurable business results, not just technical features. |
| **Conversational** | Natural and clear — avoid jargon or overly corporate language. |
| **Technical but accessible** | Demonstrates expertise while remaining clear and relevant to data leaders. |
| **Customer-centric** | Focus on how Indicium AI solves pain points, not just what it does. |

### What Indicium AI is not

- Not an offshore/nearshore outsourcing firm (global specialist, not regional staffing).
- Not vague — always focus on specific problems and measurable outcomes.
- Not buzzword-heavy — "transformation" and "innovation" must be tied to a clear result.
- Not jargon-first — avoid "synergy", "best-in-class", "cutting-edge" without definition.

---

## Visual Design System

### Spacing Rhythm

All spacing must follow multiples of **8px**: `8 / 16 / 24 / 32 / 48px`. No arbitrary values.

### Interaction Design

- Hover states: smooth transitions (`transition: all 0.2s ease` or similar).
- Consistent border-radius across interactive elements.
- Clear focus states for accessibility.

### Dashboard Design Patterns

- Sidebar or top nav for multi-section layouts.
- KPI stat cards at the top when metrics are involved.
- Interactive elements (tabs, filters, tooltips) where they add value.
- Use **D3.js** for force graphs or scatter plots; **Chart.js** for bar/line/pie charts.
- Use **Lucide Icons** for UI icons.
- White background with Vibrant Blue accent; high information density.

### Deck / Presentation Design Patterns

- Dark navy (`#1c1d2f`) background.
- One `<div class="slide">` per slide with `active` class on the first.
- Keyboard arrow navigation (ArrowLeft / ArrowRight).
- Dot indicators + prev/next buttons at the bottom.
- Structure: Cover → Agenda → Content slides → Closing/CTA.
- Smooth slide transitions.

### Guide / Document Design Patterns

- Clean layout with clear type hierarchy.
- Consistent section headings and subheadings.
- White or near-white background.
- Vibrant Blue for accents and callout boxes.

---

## Company Context (for copy generation)

### Scale & Impact Stats

| Metric | Value |
|--------|-------|
| Certified experts | 600 |
| Enterprise engagements | 500+ |
| Enterprise clients | 50+ |
| Global locations | 5 |
| Regions | AMER · LATAM · EUROPE |
| Delivery speed | Up to 4× faster |
| Performance improvement | Up to 90% |
| Reliability & accuracy | 99% |
| Cost reduction | Up to 65% |
| Average ROI | 300% |

### Target Industries

- Financial Services & Insurance
- Energy & Utilities
- Healthcare & Life Sciences
- Media & Telecommunications
- Retail & CPG
- Manufacturing

### Key Partners

Anthropic · Databricks · AWS · OpenAI · Microsoft

### Standard Boilerplate

> Indicium AI is trusted by the world's leading enterprises to deliver AI into production at scale. We are a global AI-native consultancy with proven experience across Financial Services, Energy & Utilities, Healthcare & Life Sciences, Retail & CPG, and Manufacturing. From strategy, to build, to business outcomes, we unlock value from AI with unmatched clarity, speed, and capability.
>
> Powered by 600 AI experts serving 50+ enterprise clients from 5 global locations, we work side-by-side with top partners — including Anthropic, Databricks, AWS, OpenAI, and Microsoft — to deliver modern AI with speed and measurable impact.

---

## Quick-Reference Checklist for AI-Generated Designs

Use this checklist before delivering any visual artifact:

- [ ] Fonts: Inter for all text; Roboto Mono only for labels/buttons/chips.
- [ ] Colors: only use the six palette colors defined above; no arbitrary hex values.
- [ ] Spacing: all gaps are multiples of 8px.
- [ ] Logo: correct asset for the background (white logo on dark, color logo on light).
- [ ] Tone: copy is direct, outcome-driven, and free of empty jargon.
- [ ] Hover states: smooth transitions on all interactive elements.
- [ ] Type hierarchy: document title → page title → subtitle → body → caption is visually clear.
- [ ] No external dependencies beyond Google Fonts and approved CDN libraries.
- [ ] Responsive: `<meta name="viewport">` present; layout degrades gracefully on smaller screens.
