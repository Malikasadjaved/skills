# CSS Architecture & Organization

## Cascade Layers

`@layer` controls the specificity cascade without specificity hacks. Layers
are ordered by priority — later layers ALWAYS override earlier layers,
regardless of selector specificity.

```css
/* Define layer order (first = lowest priority, last = highest) */
@layer reset, base, layout, components, utilities, overrides;

/* ── Reset layer ──────────────────────────────────── */
@layer reset {
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  img, svg { display: block; max-width: 100%; }
  button { font: inherit; cursor: pointer; }
}

/* ── Base layer ───────────────────────────────────── */
@layer base {
  html { font-size: 100%; }
  body { font-family: var(--font-body); background: var(--color-bg); color: var(--color-text); }
  h1, h2, h3 { font-family: var(--font-display); }
  a { color: var(--color-accent); }
}

/* ── Layout layer ─────────────────────────────────── */
@layer layout {
  .container { max-width: var(--container-lg); margin-inline: auto; padding-inline: var(--space-lg); }
  .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-lg); }
}

/* ── Components layer ─────────────────────────────── */
@layer components {
  .card { background: var(--color-surface); border: 1px solid var(--color-border); padding: var(--space-lg); }
  .btn { /* button styles */ }
}

/* ── Utilities layer (always wins) ────────────────── */
@layer utilities {
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; }
}
```

**Key rule**: components layer uses class selectors (`.card`, `.btn`) — never
ID selectors or element selectors. Base layer uses element selectors (`h1`,
`a`). This keeps the cascade predictable.

## Custom Properties Strategy

### Token tiers

```
Design tokens (abstract)     →  Semantic tokens    →  Component tokens
─────────────────────────        ────────────────      ──────────────────
--hue: 38                        --color-bg: ...        --btn-bg: ...
--sat-neutral: 5%                --color-text: ...      --card-border: ...
--font-display: "..."            --space-md: ...        --heading-size: ...
```

Design tokens are the raw values. Semantic tokens apply them to roles.
Component tokens are component-specific (rarely needed — prefer semantic).

### Don't over-tokenize

Only create a custom property if the value:
1. Appears 3+ times in the codebase
2. Changes in a media query or theme
3. Is a design decision that needs a single source of truth

A color used once in one component doesn't need a token. A color used in
every card, button, and link does.

### Scope tokens appropriately

```css
/* Global — defined on :root */
:root {
  --color-bg: hsl(40, 5%, 4%);
  --font-body: "JetBrains Mono", monospace;
}

/* Theme-specific */
[data-theme="dark"] {
  --color-bg: hsl(40, 5%, 4%);
}
[data-theme="light"] {
  --color-bg: hsl(40, 5%, 96%);
}

/* Component-scoped (only needed if the component varies independently) */
.card {
  --card-padding: var(--space-lg);
  padding: var(--card-padding);
}
.card--compact {
  --card-padding: var(--space-md);
}
```

## Naming Convention

Use a BEM variant. Three key rules:

1. **Block**: The component name in PascalCase or kebab-case (pick one, be
   consistent). Use kebab-case for standard CSS, PascalCase for CSS-in-JS.
2. **Element**: `block__element` — a dependent part of the block.
3. **Modifier**: `block--modifier` or `block__element--modifier` — a variant.

```css
/* Block */
.skill-card { }

/* Elements */
.skill-card__title { }
.skill-card__description { }
.skill-card__install-block { }

/* Block modifier */
.skill-card--featured { }
.skill-card--compact { }

/* Element modifier */
.skill-card__install-block--copied { }
```

### When NOT to use BEM

- Single-element components (just use the block name)
- Utility classes (`.flex`, `.sr-only`, `.hidden`)
- Layout primitives (`.container`, `.grid`)
- State that's purely for JS hooks (use data attributes: `[data-state="open"]`)

## Specificity Management

### The specificity scale (from lowest to highest)

```
0-0-0: * (universal)
0-0-1: Type selectors (h1, p, a)
0-1-0: Class selectors (.card), attribute selectors ([data-state])
0-1-1: Type + class (p.card)
1-0-0: ID selectors (#app) — NEVER use for styling
```

### Rules for low-specificity CSS

1. **Never use ID selectors** for CSS. IDs are for JavaScript and ARIA, not style.
2. **Maximum nesting depth: 3 levels.** Ideally 1–2.
3. **Use `:where()` for zero-specificity utilities:**

```css
/* :where() has specificity 0-0-0 — easy to override */
:where(.text-muted) { color: var(--color-text-muted); }
```

4. **Use cascade layers over specificity battles.** Instead of `.card .card__title`
to override `.card h3`, put components in a layer above base styles.

5. **Data attributes for state, not classes:**

```html
<!-- Better than .card--open, .card--closed, .card--loading -->
<div class="card" data-state="open" data-loading="true">
```

```css
.card[data-state="open"] { /* open styles */ }
.card[data-loading="true"] { /* loading styles */ }
```

## Modern CSS Techniques

### Container Queries

Style elements based on their container's size, not the viewport:

```css
.card-grid {
  container-type: inline-size;
  container-name: card-grid;
}

@container card-grid (min-width: 600px) {
  .card { flex-direction: row; }
}
```

### Fluid Type with clamp()

```css
:root {
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-2xl: clamp(1.8rem, 1.2rem + 2vw, 3rem);
}
```

### `has()` Selector (Parent-Child logic)

```css
/* Style the card that contains an image */
.card:has(img) { grid-column: span 2; }

/* Style the field that contains an invalid input */
.field:has(input:invalid) .field__error { display: block; }

/* Style the nav when a menu is open */
nav:has([aria-expanded="true"]) { background: var(--color-surface); }
```

### CSS Nesting (native)

```css
.card {
  background: var(--color-surface);

  & .card__title { font-size: 1.5rem; }

  &:hover { border-color: var(--color-accent); }

  &[data-featured="true"] {
    border-color: var(--color-accent);
    & .card__title { color: var(--color-accent); }
  }
}
```

## Responsive Design Methodology

### Mobile-first (preferred)

Start with the smallest layout, add complexity as space increases:

```css
/* Mobile (default) */
.grid { display: grid; grid-template-columns: 1fr; gap: 16px; }

/* Tablet */
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop */
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); gap: 24px; }
}
```

### Breakpoint variables

```css
:root {
  --bp-sm: 640px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
}

@media (min-width: var(--bp-md)) { /* tablet+ */ }
```

### Testing at every breakpoint

Always test at:
- 320px (iPhone SE — the narrowest phone still in use)
- 375px (iPhone standard)
- 768px (iPad portrait)
- 1024px (iPad landscape / small laptop)
- 1280px (standard laptop)
- 1440px+ (large desktop — does content have a max-width?)

The presence of a horizontal scrollbar at any width >= 320px is a bug.

## Performance Patterns

### Font loading

```html
<!-- Preconnect to font CDN -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- Load fonts with display=swap to prevent FOIT -->
<link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
```

In CSS, provide a reasonable fallback stack and use `font-display: swap`:

```css
:root {
  --font-display: "Cormorant Garamond", "Times New Roman", serif;
  --font-body: "JetBrains Mono", "Courier New", monospace;
}
```

### GPU-friendly animations

Only these properties animate without causing layout/paint recalculation:
- `transform` (translate, scale, rotate, skew)
- `opacity`

```css
/* BAD — triggers layout on every frame */
.animate { transition: width 0.3s, height 0.3s; }

/* GOOD — composite-only */
.animate {
  transform: scale(0.95);
  opacity: 0;
  transition: transform 0.3s, opacity 0.3s;
}
```

### CSS Containment

```css
/* Tells browser: this element's layout/paint is independent of the rest of the page */
.card-list { contain: layout style; }

/* Strict containment — use when the element's dimensions are fixed */
.avatar { contain: strict; }

/* Content containment — most versatile */
.card { contain: content; }
```

## CSS Reset (Minimal)

```css
@layer reset {
  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html {
    -webkit-text-size-adjust: 100%;
    scroll-behavior: smooth;
  }

  body {
    min-height: 100vh;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  img, picture, video, canvas, svg {
    display: block;
    max-width: 100%;
    height: auto;
  }

  input, button, textarea, select {
    font: inherit;
    color: inherit;
  }

  button {
    cursor: pointer;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  ul, ol {
    list-style: none;
  }

  /* Remove animations for users who prefer reduced motion */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
    html { scroll-behavior: auto; }
  }
}
```
