# UX Laws for Frontend Design

Each law is stated, explained, and applied directly to frontend implementation.

## Interaction Laws

### Fitts's Law
**"The time to acquire a target is a function of the distance to and size of the target."**

Application:
- Make primary actions large and positioned near the natural cursor path
- Button minimum size: 44×44px (WCAG touch target)
- Place destructive or dangerous actions away from common click zones
- Form submit buttons should be large and positioned at the form's natural endpoint
- Mobile: place primary actions in the thumb zone (bottom half of screen)

```css
/* Poor — small, hard to click */
.btn-sm { padding: 4px 8px; font-size: 11px; }

/* Good — meets minimum touch target */
.btn { padding: 12px 24px; min-height: 44px; min-width: 44px; }
```

### Hick's Law
**"Decision time increases with the number and complexity of choices."**

Application:
- Limit navigation to 5–7 items maximum
- Break complex forms into steps (wizard pattern)
- Use progressive disclosure — show common options, hide advanced ones behind an expand
- Filter/sort controls should offer 3–5 options, not 20
- Onboarding: show one thing at a time, not a feature dump

```html
<!-- Poor — 15 nav items -->
<nav>
  <a href="/">Home</a>
  <a href="/products">Products</a>
  <a href="/services">Services</a>
  <a href="/solutions">Solutions</a>
  <!-- ... 11 more ... -->
</nav>

<!-- Good — 5 top-level items, rest in dropdown -->
<nav>
  <a href="/">Home</a>
  <a href="/products">Products</a>
  <a href="/docs">Docs</a>
  <a href="/pricing">Pricing</a>
  <details><summary>More</summary><!-- secondary items --></details>
</nav>
```

### Doherty Threshold
**"Productivity soars when the computer and its user interact at a pace (<400ms) that ensures neither has to wait on the other."**

Application:
- Show loading indicators for operations > 300ms
- Use optimistic UI updates (show the result before the server confirms)
- Skeleton screens feel faster than spinners
- Debounce search input (300ms) but show results immediately
- Prefetch data before the user asks for it (hover intent, viewport proximity)

## Cognitive Laws

### Miller's Law
**"The average person can keep 7 (±2) items in their working memory."**

Application:
- Chunk form fields into groups of 5–7
- Phone numbers: 3-3-4 grouping, not continuous digits
- Credit card: 4-4-4-4 grouping
- Lists in UI should be 5–9 items; paginate beyond that
- Navigation: 5–7 top-level items maximum

### Cognitive Load
**"Minimize the mental resources required to understand and interact with an interface."**

Application:
- Use familiar patterns (don't invent new interaction models)
- Consistent placement: the search bar stays in the same spot on every page
- Visual hierarchy reduces cognitive load — the eye naturally finds what's important
- Error messages should say what happened AND what to do about it

```html
<!-- Poor — mysterious error -->
<div class="error">Error 409</div>

<!-- Good — explains what and how to fix -->
<div class="error" role="alert">
  <strong>This document already exists.</strong>
  Try a different title or edit the existing one.
  <button>View existing document</button>
</div>
```

### Serial Position Effect
**"Users remember the first and last items in a series best."**

Application:
- Place the most important nav item first (left/top)
- Place the primary CTA last (right/bottom) in a button group
- Pricing tables: highlight the middle option, but make the "best value" tag prominent
- Put critical info at the start and a strong CTA at the end of landing pages

### Von Restorff Effect
**"The item that differs from the rest is most memorable."**

Application:
- Make the primary CTA visually distinct (different color, slightly larger)
- A single animated element among static ones draws attention
- Your "one memorable thing" leverages this law
- Don't overuse: if everything is special, nothing is

### Zeigarnik Effect
**"People remember incomplete tasks better than completed ones."**

Application:
- Progress bars leverage this (people want to finish)
- "Complete your profile — 3 of 5 steps done" creates engagement
- Onboarding flows with clear step counts
- Save-for-later / watchlist features

## Decision Laws

### Choice Overload (Paradox of Choice)
**"Too many options cause decision paralysis and dissatisfaction."**

Application:
- Pricing: 3 tiers maximum (basic, pro, enterprise)
- Feature comparison: highlight 5–7 key differences, not 30
- Category filters: top 5 categories + "more" dropdown
- Landing page: one primary CTA, one secondary

### Peak-End Rule
**"People judge an experience by its peak and its end, not the average."**

Application:
- The page-load animation is the "peak" — make it memorable
- Form submission success state = the "end" — make it delightful
- Error states shouldn't be painful (friendly copy, clear next action)
- The checkout confirmation page matters disproportionately

### Jakob's Law
**"Users spend most of their time on other sites. They prefer yours to work the same way."**

Application:
- Place logo at top-left (linking to home)
- Search icon = magnifying glass, not something creative
- Underlined text = link; blue text = link
- Hamburger menu = navigation (mobile)
- Stick to platform conventions (Cmd/Ctrl+S saves)

## Visual Perception (Gestalt)

### Law of Proximity
**"Objects near each other are perceived as grouped."**

Application:
- Form labels should be closer to their input than to the next label
- Section spacing should be larger than inter-element spacing
- Related links in a group; unrelated links visibly separated

```css
/* Section gap > element gap */
.section + .section { margin-top: 64px; }   /* unrelated */
.field + .field     { margin-top: 16px; }   /* related */
label + input       { margin-top: 4px; }    /* tightly coupled */
```

### Law of Similarity
**"The eye groups similar elements together."**

Application:
- All primary buttons share the same style
- All links within body text share the same color
- Cards in the same category share visual treatment
- Color-coded sections: consistent color = consistent meaning

### Law of Common Region
**"Elements within a bounded area are perceived as a group."**

Application:
- Card containers group related content
- Fieldset borders group related form fields
- Sidebar background distinguishes navigation from content
- Modal overlay groups the dialog content visually

### Law of Prägnanz (Simplicity)
**"People interpret complex images in the simplest form possible."**

Application:
- Icons should be the simplest form that conveys meaning
- Don't use complex illustrations where simple icons work
- Data visualizations: remove non-data ink (Tufte's principle)
- Whitespace simplifies: empty space reduces perceived complexity

## Practical Cheatsheet

| UX Problem | Law to Apply | Quick Fix |
|---|---|---|
| Users miss the CTA button | Fitts's Law + Von Restorff | Make it larger, distinct color, positioned prominently |
| Users abandon long forms | Hick's Law + Cognitive Load | Break into steps, show progress |
| Users don't read error messages | Cognitive Load | Say what happened + what to do, in plain language |
| Navigation feels overwhelming | Miller's Law + Hick's Law | 5–7 items max, group secondary items |
| Page feels "wrong" but can't say why | Gestalt Proximity | Check spacing: related things closer, unrelated farther |
| Users don't complete onboarding | Zeigarnik + Peak-End | Show step count, make completion feel rewarding |
| Interaction feels slow | Doherty Threshold | Skeleton screens, optimistic updates, prefetch |
