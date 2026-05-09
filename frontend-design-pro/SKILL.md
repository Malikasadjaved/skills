---
name: frontend-design-pro
description: >
  Production-grade frontend design skill — builds distinctive, polished
  interfaces using concrete visual-design rules, UX laws, typography
  science, color accessibility, CSS architecture, and motion principles.
  This is an enhanced, research-backed alternative to the official
  frontend-design skill with 28 concrete design rules, component state
  design, accessibility requirements, and a pre-implementation quality
  checklist. Use when building or redesigning web pages, components,
  landing pages, or full applications.
triggers:
  - frontend design
  - web design
  - UI design
  - landing page
  - web page design
  - beautiful design
  - modern website
  - redesign
  - make it look good
  - polished UI
  - professional design
  - build a page
  - create a UI
  - design a component
  - HTML CSS
  - web interface
version: 1.0.0
author: malikasadjaved
---

## Overview

This skill produces production-grade frontend that is both visually striking
and technically sound. It combines creative design direction with concrete,
research-backed rules for visual design, typography, color science, layout
systems, motion, accessibility, and CSS architecture.

**What this skill covers (that the official frontend-design skill does not):**

- **28 concrete visual design rules** — shadows, borders, spacing, color,
  optical alignment, typography — drawn from research and professional practice
- **UX law applications** — Fitts's, Hick's, Miller's, Gestalt principles,
  Peak-End rule — applied directly to interface decisions
- **Color science** — HSL/OKLCH manipulation, WCAG contrast compliance,
  palette generation algorithms, dark-mode strategy
- **Typography system** — modular scales, fluid type with clamp(), line-height
  ratios, measure (line-length) limits, font pairing methodology
- **Layout and spacing system** — 8px grid, spacing scales, inner vs. outer
  padding, 12-column grids, optical vs. mathematical alignment
- **Motion design** — duration guidelines, easing-curve selection, what to
  animate vs. leave static, reduced-motion fallbacks, GPU-friendly properties
- **CSS architecture** — cascade layers, specificity discipline, naming
  conventions (BEM variant), custom properties strategy, critical CSS
- **Component state design** — loading, empty, error, success, active, focus,
  disabled, hover states — every component covers all states
- **Accessibility** — WCAG 2.1 AA minimum, focus-ring design, semantic HTML,
  screen-reader considerations, touch-target sizing
- **Performance** — font-loading strategy, animation performance (composite-only
  properties), CSS containment, critical rendering path
- **Anti-patterns catalog** — common mistakes and how to fix them
- **Pre-implementation checklist** — what to define before writing code
- **Quality audit** — systematic review of the finished interface

## Design Thinking

Before writing any code, answer these four questions:

### 1. Purpose
What problem does this interface solve? Who uses it, and in what context?
A developer tool landing page needs different visual language than a yoga
studio booking site.

### 2. Tone — Commit to ONE Bold Direction

Pick a clear aesthetic and execute it with precision. Examples:

| Direction | Characteristics | Good for |
|---|---|---|
| Brutally minimal | Helvetica/Neue, tight spacing, almost no color, extreme whitespace | Editorial, architecture, luxury |
| Maximalist chaos | Dense layouts, clashing colors, mixed type, layered elements | Creative portfolios, music, art |
| Retro-futuristic | CRT scanlines, monospace, neon accents, terminal aesthetics | Developer tools, gaming, sci-fi |
| Organic/natural | Earth tones, rounded forms, generous whitespace, serif type | Wellness, food, sustainability |
| Luxury/refined | Gold/brass accents, serif display type, generous spacing, dark palette | Premium products, finance, legal |
| Editorial/magazine | Strong typographic hierarchy, asymmetric layout, dramatic scale | Content sites, blogs, publications |
| Brutalist/raw | Visible borders, default fonts, stark contrast, "unstyled" aesthetic | Art, counter-culture, indie |
| Soft/pastel | Light palette, rounded corners, gentle shadows, friendly type | Education, kids, community |
| Industrial/utilitarian | Monospace, labels, spec-sheet styling, indicator lights | Dev tools, manufacturing, data |
| Art deco/geometric | Symmetric patterns, gold, high contrast, geometric ornaments | Hotels, events, luxury |

Importantly: **bold maximalism and refined minimalism both work** — the key is
intentionality, not intensity. Match implementation complexity to the vision.

### 3. Constraints

List technical constraints: framework (plain HTML, React, Vue), browser support
(modern only? IE11?), performance budget, accessibility level (WCAG AA
minimum), device range (mobile, tablet, desktop).

### 4. Differentiation

What is the ONE thing someone will remember about this interface after seeing
it? If you can't name it, you haven't committed to a direction hard enough.
Examples: "the amber instrument lights on every card," "the brutalist
monospace headline that bleeds off the page," "the impossible smoothness of
the page-load animation."

## Visual Design Rules — The 28 Rules

These rules are drawn from professional design practice and research. They
are concrete and actionable. Apply them systematically.

### Color & Contrast

**1. Never use pure black or pure white.**
Pure black (`#000`) creates painfully high contrast against white. Pure white
(`#fff`) overwhelms the eye on dark backgrounds. Use near-black (`#0a0a0b`)
and near-white (`#f5f4f0`). In dark mode, never go lighter than `#e8e4dc`
for body text — it glows uncomfortably.

**2. Saturate your neutrals.**
Greys in the real world are never perfectly desaturated. Add 2–5% of your
interface's hue to every grey. For a warm design: `hsl(40, 4%, 30%)`. For
cool: `hsl(220, 4%, 30%)`. This ties the entire palette together invisibly.

**3. High contrast for importance, low contrast for structure.**
Elements users must notice (text, buttons, inputs) need strong contrast against
the background. Structural elements (dividers, card borders, drop-shadows) can
use minimal contrast — they should be discovered, not announced.

**4. Container brightness limits.**
The brightness gap between a background and its container should stay within:
- **Dark interfaces**: 12% HSB brightness difference maximum
- **Light interfaces**: 7% HSB brightness difference maximum
Cards that are too bright on dark backgrounds look like glowing tiles, not
restrained containers.

**5. Palette colors must differ in brightness, not just hue.**
If every color in your palette has the same brightness, none stands out.
Ensure each color has a distinct brightness value so the palette reads
clearly even in grayscale.

**6. Warm or cool — pick one for neutrals.**
When saturating neutrals, commit to either warm (amber, peach) or cool (blue,
slate) undertones. Mixing warm greys with cool greys creates a disharmonious
palette that feels "off" even to untrained eyes.

### Typography

**7. Letter-spacing and line-height scale inversely with text size.**
- Headlines (32px+): `letter-spacing: -0.01em`, `line-height: 1.05–1.15`
- Body (14–18px): `letter-spacing: 0`, `line-height: 1.5–1.7`
- Small labels (10–12px): `letter-spacing: 0.04–0.12em`, `line-height: 1.3–1.5`
Large text needs tighter spacing; small text needs room to breathe.

**8. Body text must be at least 16px.**
Below 16px, reading speed drops measurably. Browsers default to 16px for a
reason. Labels, captions, and legal text can go smaller (12–14px) but never
body copy.

**9. Limit line length to ~70 characters.**
The optimal reading measure is 60–80 characters per line. Wider lines make
it hard for the eye to find the next line. Narrower lines break the reading
flow. Use `max-width: 65ch` on text containers.

**10. Maximum two typefaces.**
One display/heading font + one body font. A third font is occasionally
justified for code blocks or UI labels. More than two unrelated typefaces
creates visual noise. The second typeface should contrast with the first —
pair serif + monospace, or display serif + workhorse sans-serif, never two
similar fonts.

### Layout & Spacing

**11. Everything aligns with something.**
No element floats alone. Every margin, every edge aligns with a grid line,
another element's edge, or a mathematically related position. Misaligned
elements register as "wrong" even when the viewer can't articulate why.

**12. Use a consistent spacing scale.**
All padding, margin, and gap values come from a single scale. The standard
is multiples of 8px: `4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 120`.
Never use arbitrary values like `7px`, `13px`, `23px`.

**13. Order elements by visual weight — heaviest on the outside.**
In any layout group, arrange elements from heaviest (largest, boldest, darkest)
to lightest (smallest, thinnest, faintest). Heavier elements anchor the edges;
lighter elements sit inside. Think of a triangular composition.

**14. Use a 12-column horizontal grid.**
12 divides into 1, 2, 3, 4, and 6 columns — the most flexible denominator.
Even if your layout uses only 2 or 3 columns, the 12-column grid provides
a consistent measurement system.

**15. Outer padding must be >= inner padding.**
Elements inside a container are more related to each other than to the
container edges. If card padding is 24px, the gap between cards should be
20–24px, and the section padding around the card grid should be >= 24px.

**16. Measure spacing between high-contrast edges, not element boundaries.**
The visual space between a heading and a paragraph isn't the CSS margin
between their boxes — it's the distance from the heading's text baseline
to the paragraph's text cap-height. When alignment looks wrong, measure
from the visible contrast point, not the box-model edge.

### Containers, Borders & Depth

**17. Container borders need dual contrast.**
A container border must be lighter than BOTH the container background AND
the page background (or darker than both in light mode) for the edge to read
clearly. A border that's between the two brightnesses appears to belong to
neither side.

**18. Nest corner radii mathematically.**
`inner_radius = outer_radius - padding`. If a card has `border-radius: 8px`
and 16px padding, the inner element gets `border-radius: 4px` (use `max(0, ...)`
to prevent negative values). This creates concentric, non-competing corners.

**19. Never stack hard visual divisions.**
Don't place a card border directly next to a section background change, or
a divider line directly adjacent to a container edge. Two hard edges side by
side create visual clutter. Leave at least one spacing unit between divisions.

### Shadows & Depth

**20. Closer elements should be lighter.**
In the physical world, objects nearer to a light source appear brighter.
In both light and dark interfaces, elevated surfaces (modals, tooltips,
dropdowns) should be slightly lighter than the surface beneath them.

**21. Shadow blur = 2× the vertical offset.**
If a shadow drops 4px on the Y axis, use 8px blur. Increase opacity as the
element rises higher (more elevation). Never use `box-shadow` without a blur
value — hard shadows look like rendering errors.

**22. Don't use shadows in dark interfaces.**
Shadows on dark backgrounds are invisible (shadow is darker than the
background). Use a lighter border or a subtle brightness increase for the
elevated element instead. If you must use shadow, add a hard 1px lighter
edge so the shadow reads against it.

**23. Pick one depth technique and use it consistently.**
Either soft shadows, hard shadows, or no shadows (border-only elevation).
Mixing shadow styles within one interface breaks the depth model and confuses
the user's spatial understanding.

### Buttons & Interactive Elements

**24. Horizontal padding = 2× vertical padding on buttons.**
The standard button has `padding: 12px 24px` (vertical 12, horizontal 24).
This ratio reinforces the expected wider-than-tall button shape. Deviation
signals a non-standard element.

**25. Icons need less contrast than the text they accompany.**
Icons are usually heavier (more filled pixels) than the text beside them.
Reduce icon opacity to 80–90% of the text color, or lighten the icon color
slightly. The text and icon should feel like they have equal visual weight.

### Composition & Hierarchy

**26. Every design decision must be defensible.**
If someone points at any part of the interface and asks "why does this look
this way?", you should have an answer. "It's the default" is not an answer.
Every color, every spacing value, every font choice must be intentional.

**27. Optical alignment beats mathematical alignment.**
Round shapes (circles, icons, buttons with border-radius) have a visual center
that differs from their mathematical bounding-box center. Align by eye —
nudge elements until they "feel" centered. This matters most for play buttons
in circles, icons next to text, and vertically centering asymmetric shapes.

**28. Complex backgrounds need simple foregrounds (and vice versa).**
A richly textured background (gradient mesh, noise, geometric pattern) demands
clean, minimal foreground elements. A plain background can support complex,
dense foreground content. Never put complex content on a complex background.

## Typography System

### Font Selection

**Display/Heading font qualities to seek:**
- Distinctive character (serifs, unusual proportions, unique terminals)
- Works at large sizes (36px+)
- Has at least regular + bold weights
- Avoid: Inter, Roboto, Arial, Helvetica, system fonts — these are overused
  and signal "default"

**Body font qualities to seek:**
- High legibility at 14–18px
- Regular, italic, bold, bold-italic weights
- Good language coverage for your content
- Complements but contrasts with the display font

**Code/monospace font:**
- JetBrains Mono, Fira Code, IBM Plex Mono, or Geist Mono
- Clear distinction between similar characters (0/O, 1/l/I, i/j)
- Works at 12–15px without breaking up

### Modular Type Scale

Use a ratio-based scale. The classic choices:
- `1.25` (major third) — restrained, good for dense content
- `1.333` (perfect fourth) — balanced, most versatile
- `1.5` (perfect fifth) — dramatic, for editorial/hero use

Example with base 16px and ratio 1.333:
```
text-xs:   12px  (0.75rem)
text-sm:   14px  (0.875rem)
text-base: 16px  (1rem)
text-lg:   19px  (1.1875rem)
text-xl:   25px  (1.5625rem)
text-2xl:  33px  (2.0625rem)
text-3xl:  44px  (2.75rem)
text-4xl:  59px  (3.6875rem)
```

### Fluid Typography

Use `clamp()` for type that scales with the viewport without breakpoints:

```css
:root {
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-xl: clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem);
  --text-4xl: clamp(2.5rem, 1.5rem + 4vw, 5rem);
}
```

## Color System

### Color Space

Use **HSL** or **OKLCH** for programmatic color manipulation — never RGB hex
for derived colors. HSL lets you vary saturation and lightness while keeping
hue constant. OKLCH is perceptually uniform (equal numeric changes look like
equal visual changes).

### Palette Construction

1. Choose a single base hue
2. Vary lightness (L in HSL) from ~5% to ~95% to create the grey-like tones
3. Vary saturation: low (5–15%) for neutrals, medium (40–70%) for accents,
   high (80–100%) sparingly
4. Create 2–3 accent variants by shifting hue 15–30° and adjusting saturation

### WCAG Contrast Compliance

Minimum contrast ratios (AA standard):
- Body text (< 18px): **4.5:1** against background
- Large text (>= 18px bold or >= 24px): **3:1** against background
- UI components and graphical objects: **3:1** against adjacent colors
- AAA (enhanced): 7:1 for body, 4.5:1 for large

**Never rely on eyeballing contrast.** Use a contrast checker. Colors that
"feel like enough contrast" often fail WCAG AA.

### Dark Mode Strategy

- Backgrounds: `hsl(X, 5%, 4–8%)` range
- Surfaces: `hsl(X, 5%, 10–14%)` range
- Text: `hsl(X, 10%, 85–92%)` — never pure white
- Accent colors need higher lightness to maintain contrast on dark backgrounds
- Drop shadows are invisible — use lighter borders or brightness elevation

## Layout & Spacing System

### 8px Grid

All spacing values are multiples of 8px. The standard scale:

| Token | Value | Use |
|---|---|---|
| `space-xs` | 4px | Tight icon-label gaps, inline spacing |
| `space-sm` | 8px | Related elements within a component |
| `space-md` | 16px | Default gap between components |
| `space-lg` | 24px | Section padding, card padding |
| `space-xl` | 32px | Large section gaps |
| `space-2xl` | 48px | Major layout divisions |
| `space-3xl` | 64px | Hero/header spacing |
| `space-4xl` | 96px | Section separation |

### Container Widths

```css
:root {
  --container-sm: 640px;   /* narrow reading */
  --container-md: 768px;   /* compact content */
  --container-lg: 1024px;  /* standard content */
  --container-xl: 1280px;  /* wide layouts */
}
```

### Responsive Breakpoints

Test at these minimum widths:
- **320px**: Small phone (iPhone SE)
- **375px**: Standard phone (iPhone)
- **414px**: Large phone
- **768px**: Tablet portrait
- **1024px**: Tablet landscape / small desktop
- **1280px**: Standard desktop
- **1440px**: Large desktop
- **1920px**: Full HD (cap the max-width here)

## Motion & Animation

### What to Animate

Focus on high-impact moments:
- **Page/component entry**: One orchestrated stagger with `animation-delay`
  creates more delight than scattered micro-interactions
- **State transitions**: Hover, focus, active — subtle, fast (150–200ms)
- **Layout shifts**: When elements enter/exit the DOM unexpectedly
- **Feedback**: Button press, copy confirmation, form submission

### Duration Guidelines

| Interaction | Duration | Easing |
|---|---|---|
| Hover on/off | 150–200ms | `ease-out` / `ease-in` |
| Toggle/expand | 200–300ms | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Page transition | 300–500ms | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Complex orchestration | 400–600ms | `cubic-bezier(0.22, 0.61, 0.36, 1)` |
| Micro-interaction | 100–150ms | `ease-out` |

### GPU-Friendly Properties

Only animate **composite** properties when possible (they don't trigger layout
or paint):
- `transform` (translate, scale, rotate)
- `opacity`
- `filter` (use sparingly — can be expensive at high resolutions)

**Never animate:** `width`, `height`, `top`, `left`, `margin`, `padding`,
`border-width` — these trigger layout recalculation on every frame.

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## CSS Architecture

### Cascade Layers

Use `@layer` to control the specificity cascade:

```css
@layer reset, base, layout, components, utilities, overrides;
```

- **reset**: CSS reset/normalize
- **base**: Element selectors (body, h1–h6, a, p), typography defaults
- **layout**: Grid systems, container, section spacing
- **components**: BEM-style component blocks
- **utilities**: Single-purpose helper classes
- **overrides**: Last-resort specificity (use sparingly)

### Custom Properties Strategy

```css
:root {
  /* Design tokens — the only source of truth */
  --color-bg: hsl(40, 5%, 4%);
  --color-surface: hsl(40, 5%, 9%);
  --color-text: hsl(40, 10%, 88%);
  --color-text-muted: hsl(40, 5%, 55%);
  --color-accent: hsl(38, 60%, 55%);
  --font-display: "Cormorant Garamond", Georgia, serif;
  --font-mono: "JetBrains Mono", monospace;
  --space-unit: 8px;
  --radius: 2px;
}
```

### Naming Convention

Use a BEM variant with single-dash separators for blocks and double-dash
for modifiers. Avoid nesting beyond 3 levels deep.

```css
/* Block */
.skill-card { }

/* Element */
.skill-card__title { }
.skill-card__install-block { }

/* Modifier */
.skill-card--featured { }
```

### Specificity Discipline

- Never use ID selectors in CSS
- Keep specificity as flat as possible (0–2 levels of selector nesting)
- Use `:where()` to zero-out specificity when creating utility classes
- Prefer cascade layers over specificity battles

## Component Design Patterns

### Every Component Must Handle ALL States

For EVERY interactive component, define:
- **Default** — resting state
- **Hover** — cursor is over the element
- **Focus** — keyboard focused (visible focus ring — NEVER remove outline
  without replacing it)
- **Active** — being pressed/clicked
- **Disabled** — non-interactive, visually dimmed
- **Loading** — async operation in progress (spinner, skeleton, shimmer)
- **Empty** — no data to display (illustration + helpful message)
- **Error** — operation failed (error message + retry action)
- **Success** — operation completed (brief confirmation)

### Forms

```html
<!-- Every input needs: label, placeholder, helper text, error state -->
<div class="field">
  <label for="email" class="field__label">Email address</label>
  <input id="email" type="email" class="field__input"
         placeholder="you@example.com"
         aria-describedby="email-help"
         required />
  <span id="email-help" class="field__helper">We'll never share your email.</span>
  <span class="field__error" role="alert" hidden>Please enter a valid email.</span>
</div>
```

### Buttons

```css
.btn {
  --btn-bg: var(--color-accent);
  --btn-text: var(--color-bg);

  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 24px;  /* H-padding = 2× V-padding */
  min-height: 44px;     /* WCAG touch target minimum */
  font: inherit; font-weight: 500; font-size: 14px;
  background: var(--btn-bg); color: var(--btn-text);
  border: none; border-radius: var(--radius);
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.btn:hover { opacity: 0.9; }
.btn:active { transform: scale(0.98); }
.btn:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; pointer-events: none; }
```

## Accessibility Requirements

### Minimum Compliance (WCAG 2.1 AA)

- All text meets contrast minimums (4.5:1 body, 3:1 large)
- All interactive elements have visible focus indicators
- All inputs have associated `<label>` elements
- All images have `alt` text (decorative images use `alt=""`)
- Page has exactly one `<h1>` and a logical heading hierarchy
- `aria-label` on elements with no visible text (icon buttons)
- Touch targets are at least 44×44px
- Page is fully navigable by keyboard (Tab, Enter, Escape)
- `prefers-reduced-motion` is respected
- `prefers-color-scheme` is respected
- No `<div>` or `<span>` used as a button — use `<button>`

### Focus Ring Design

```css
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
/* Remove the default outline but ALWAYS replace it */
:focus { outline: none; }
:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
```

## Performance

### Font Loading

```html
<!-- Preconnect to font origin -->
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<!-- Use font-display: swap to prevent FOIT (flash of invisible text) -->
<link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
```

### Animation Performance

Only animate composite properties (`transform`, `opacity`). When using
`transform` for positioning, use `translate3d` to force GPU layer promotion
on older browsers:

```css
.animate-in {
  transform: translate3d(0, 24px, 0);
  opacity: 0;
  transition: transform 0.4s ease, opacity 0.4s ease;
}
.animate-in.visible {
  transform: translate3d(0, 0, 0);
  opacity: 1;
}
```

### CSS Containment

Use `contain` to limit layout/paint recalculations for off-screen or
self-contained components:

```css
.card { contain: content; }  /* limits layout + paint scope */
```

## Anti-Patterns

| Anti-Pattern | Why it fails | Fix |
|---|---|---|
| Purple gradient on white | Overused, signals "AI-generated" | Use contextual colors, unique palette |
| Inter/Roboto/Arial as display font | Generic, no character | Use distinctive display fonts |
| Removing `:focus-visible` without replacing it | Keyboard users can't navigate | Always provide visible focus indicator |
| Animating `width`/`height` | Layout thrashing, jank | Use `transform: scale()` |
| Centered 600px container for everything | Boring, no layout creativity | Vary container widths, use asymmetry |
| `box-shadow` with no blur | Looks like a rendering glitch | Always set blur >= 1px |
| Pure black background | Harsh, uncomfortable to look at | `#0a0a0b` or near-black |
| `text-align: center` on paragraphs | Hard to read, amateurish | Left-align body text; center only headings |
| Div-as-button | Not focusable, no ARIA role | Use `<button>` — it's free accessibility |
| No `alt` on images | Screen readers can't describe content | Every `<img>` gets `alt` |

## Pre-Implementation Checklist

Before writing a single line of code, define:

- [ ] **Aesthetic direction** — one sentence that captures the visual concept
- [ ] **Color palette** — background, surface, text, text-muted, accent, border (6 tokens minimum)
- [ ] **Font pair** — one display font, one body font
- [ ] **Spacing scale** — at minimum: xs, sm, md, lg, xl, 2xl
- [ ] **The "one memorable thing"** — the detail someone will remember
- [ ] **Component inventory** — list every component needed and its states
- [ ] **Breakpoint plan** — which breakpoints and what changes at each
- [ ] **Animation plan** — which moments animate, durations, easing curves

## Quality Audit Checklist

After implementation, verify:

- [ ] All 28 visual design rules considered (explicitly reject any that
  don't apply)
- [ ] Color contrast passes WCAG AA for all text
- [ ] Focus rings visible on all interactive elements
- [ ] All images have alt text
- [ ] Heading hierarchy is logical (h1 → h2 → h3, no skips)
- [ ] Touch targets >= 44×44px
- [ ] Page works at 320px width (horizontal scroll bar is a bug)
- [ ] Page works at 1920px width (content doesn't dissolve)
- [ ] Reduced-motion query respected
- [ ] No layout thrashing (check DevTools Performance tab)
- [ ] Fonts load with swap strategy (FOIT under 200ms)
- [ ] Every component handles all applicable states
- [ ] Spacing values come from the scale (no arbitrary `7px` or `13px`)
- [ ] No pure black or pure white used
- [ ] Neutral colors are saturated (2–5% of accent hue)
- [ ] Border contrast is correct (lighter than both container and background)
- [ ] The "one memorable thing" is actually visible and working

## Install

```bash
npx skills add malikasadjaved/skills@frontend-design-pro
```
