# Color Science & Systems

## Why Not RGB Hex

Hex colors (`#c8a45c`) are opaque. You cannot look at a hex value and know
how to make it lighter, darker, more saturated, or more muted. **HSL** and
**OKLCH** expose the dimensions of color as parameters you can manipulate.

### HSL (Hue, Saturation, Lightness)

```
hsl(38, 60%, 55%)
 │    │    │
 │    │    └─ Lightness: 0% = black, 50% = pure color, 100% = white
 │    └────── Saturation: 0% = grey, 100% = full chroma
 └─────────── Hue: 0–360° around the color wheel (0=red, 120=green, 240=blue)
```

**Why HSL for design systems:**
- Deriving lighter/darker variants: change L, keep H and S
- Deriving muted variants: reduce S, keep H and L
- Creating analogous colors: shift H by ±15–30°, keep S and L
- Complementary color: shift H by 180°

### OKLCH (Perceptually Uniform)

OKLCH is the modern, perceptually uniform alternative:

```
oklch(70% 0.15 38)
  │    │    │
  │    │    └─ Hue (same 0–360 as HSL)
  │    └────── Chroma (intensity, roughly 0–0.37 for sRGB)
  └─────────── Lightness (perceptually uniform, 0–100%)
```

**Why OKLCH:**
- Equal numeric steps in lightness LOOK like equal visual steps
- In HSL, `hsl(240, 100%, 50%)` (blue) and `hsl(60, 100%, 50%)` (yellow)
  have the same "lightness" but yellow is MUCH brighter — OKLCH fixes this
- Better dark-mode color generation

## Palette Construction Algorithm

### Step 1: Choose base hue

Pick one hue that defines your interface's personality:
- 0–15°: Red, aggressive, urgent (errors, sales, food)
- 20–45°: Orange/amber, warm, energetic (creative, construction)
- 40–55°: Gold/brass, premium, refined (luxury, finance, heritage)
- 180–220°: Blue, trustworthy, calm (enterprise, healthcare, banking)
- 260–290°: Purple/violet, creative, mysterious (AI, gaming, spirituality)
- 120–160°: Green/teal, natural, growth (environment, wellness, finance)

### Step 2: Generate the neutral scale

Take your base hue and create 8–10 lightness stops at very low saturation:

```css
:root {
  /* Warm neutrals (hue=40, sat=5%) for a brass/gold theme */
  --neutral-0: hsl(40, 5%, 4%);    /* near-black */
  --neutral-1: hsl(40, 5%, 8%);    /* dark surface */
  --neutral-2: hsl(40, 5%, 12%);   /* elevated surface */
  --neutral-3: hsl(40, 5%, 16%);   /* card */
  --neutral-4: hsl(40, 5%, 24%);   /* border */
  --neutral-5: hsl(40, 5%, 40%);   /* muted text */
  --neutral-6: hsl(40, 5%, 60%);   /* secondary text */
  --neutral-7: hsl(40, 5%, 80%);   /* primary text (dark bg) */
  --neutral-8: hsl(40, 5%, 92%);   /* off-white */
  --neutral-9: hsl(40, 5%, 96%);   /* near-white */
}
```

### Step 3: Generate the accent scale

Same hue, varying lightness and saturation:

```css
:root {
  --accent-0: hsl(38, 80%, 18%);   /* darkest — backgrounds, deep accents */
  --accent-1: hsl(38, 70%, 30%);   /* dark — hover states on dark bg */
  --accent-2: hsl(38, 65%, 42%);   /* mid-dark — borders, subtle accents */
  --accent-3: hsl(38, 60%, 55%);   /* BASE — primary accent */
  --accent-4: hsl(38, 65%, 65%);   /* light — hover on light bg */
  --accent-5: hsl(38, 40%, 85%);   /* lightest — subtle backgrounds */
}
```

### Step 4: Semantic tokens

Map the palette to semantic meaning:

```css
:root {
  --color-bg: var(--neutral-0);
  --color-surface: var(--neutral-1);
  --color-surface-elevated: var(--neutral-2);
  --color-border: var(--neutral-3);
  --color-border-hover: var(--neutral-4);
  --color-text: var(--neutral-7);
  --color-text-muted: var(--neutral-5);
  --color-accent: var(--accent-3);
  --color-accent-hover: var(--accent-4);
  --color-success: hsl(140, 50%, 50%);
  --color-error: hsl(0, 60%, 55%);
  --color-warning: hsl(38, 70%, 50%);
}
```

## WCAG Contrast Calculation

The contrast ratio between two colors is (L1 + 0.05) / (L2 + 0.05) where L
is relative luminance, calculated from sRGB channel values.

Rather than computing manually, use these reference tables:

### White text on dark backgrounds (AA: 4.5:1)

| Background lightness (HSL) | White `hsl(0,0%,100%)` | Off-white `hsl(40,10%,90%)` |
|---|---|---|
| L=4% | 18:1 ✓ | 15:1 ✓ |
| L=8% | 12:1 ✓ | 10:1 ✓ |
| L=12% | 9:1 ✓ | 7.5:1 ✓ |
| L=16% | 6.5:1 ✓ | 5.5:1 ✓ |
| L=30% | 3.5:1 ✗ | 3:1 ✓ (large only) |
| L=40% | 2.5:1 ✗ | 2.1:1 ✗ |

### Dark text on light backgrounds (AA: 4.5:1)

| Background lightness (HSL) | Black `hsl(0,0%,0%)` | Dark grey `hsl(40,5%,15%)` |
|---|---|---|
| L=96% | 20:1 ✓ | 14:1 ✓ |
| L=92% | 17:1 ✓ | 12:1 ✓ |
| L=85% | 13:1 ✓ | 9:1 ✓ |
| L=75% | 10:1 ✓ | 7:1 ✓ |
| L=60% | 7:1 ✓ | 4.8:1 ✓ |

General rule: for AA compliance with body text:
- Dark mode: text L >= 80%, background L <= 16%
- Light mode: text L <= 20%, background L >= 85%

## Dark Mode Color Strategy

When converting from light to dark:

1. **Backgrounds**: Light L 95–98% → Dark L 4–8%
2. **Surfaces**: Light L 100% → Dark L 8–14%
3. **Text**: Light L 10–20% → Dark L 85–92%
4. **Accent colors**: MUST increase lightness by 10–20% to maintain
   the same perceived contrast (colors look darker against dark backgrounds)
5. **Shadows**: Eliminate. Use lighter borders or brightness elevation instead.
6. **Saturation**: Reduce accent saturation by 5–10% — high saturation on
   dark backgrounds looks neon/glowing.

```css
:root {
  --color-bg: hsl(40, 5%, 96%);
  --color-surface: hsl(40, 5%, 100%);
  --color-text: hsl(40, 5%, 12%);
  --color-accent: hsl(38, 65%, 45%);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: hsl(40, 5%, 4%);
    --color-surface: hsl(40, 5%, 9%);
    --color-text: hsl(40, 10%, 88%);
    --color-accent: hsl(38, 60%, 55%);  /* +10% lightness */
  }
}
```

## Common Color Mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Same hue, same saturation, different lightness only | Boring, flat palette | Vary saturation across the scale |
| Accent color too bright on dark (L>70%) | Glowing neon effect | Keep accent L between 45–65% on dark |
| Accent color too dark on light (L<35%) | Looks muddy, invisible | Keep accent L between 40–60% on light |
| Grey neutrals (S=0%) | Sterile, lifeless | Add 2–5% saturation of your accent hue |
| Red text for errors at L=50% | Fails WCAG AA on dark or light | Error red: L=45–55% with S=60–70% |
| Pure white text on pure black | Eye strain, harsh | Off-white + near-black |
