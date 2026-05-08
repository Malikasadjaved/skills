# Playwright Screenshot — Quick Reference

## Core screenshot API

```python
await page.screenshot(path="out.png", full_page=True)
await page.screenshot(path="out.jpg", type="jpeg", quality=80)
await page.screenshot(path="out.png", clip={"x": 0, "y": 0, "width": 800, "height": 600})
element = await page.query_selector(".target")
await element.screenshot(path="element.png")
```

## Page load strategies

| `wait_until` | Waits for | Use when |
|---|---|---|
| `load` | HTML + CSS + images loaded | Simple static pages |
| `domcontentloaded` | HTML parsed, DOM ready | You'll wait for specific elements |
| `networkidle` | No network activity for 500ms | Full rendering, SPAs, lazy content |

## Browser launch flags

```python
# Production (Docker)
["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--disable-setuid-sandbox"]

# Local dev (no extra flags needed)
[]
```

## Viewport presets

| Device | Width | Height |
|---|---|---|
| Desktop HD | 1920 | 1080 |
| Desktop QHD | 2560 | 1440 |
| Laptop | 1366 | 768 |
| Tablet (iPad) | 1024 | 768 |
| Mobile (iPhone 14) | 390 | 844 |
| Mobile (Pixel 7) | 412 | 915 |

## Selectors to remove before capture

```javascript
// Cookie banners, chat widgets, sticky elements
const selectors = [
    '.cookie-banner', '.cookie-consent', '#cookie-notice',
    '#intercom-container', '.chat-widget', '#live-chat',
    '.fixed-header', '.sticky-nav', '.floating-action',
    '[data-testid="floating-action"]', '.back-to-top',
    '.newsletter-popup', '.modal-overlay',
];
selectors.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
```

## Network blocking (faster loads)

```python
# Block non-essential resources
await page.route("**/*", lambda route: route.abort()
    if route.request.resource_type in ["media", "font", "ping", "images"]
    else route.continue_())
```

## Resource types

`document`, `stylesheet`, `image`, `media`, `font`, `script`, `texttrack`, `xhr`, `fetch`, `eventsource`, `websocket`, `manifest`, `ping`, `other`

## PDF options

```python
await page.pdf(
    path="out.pdf",
    format="A4",           # or "Letter", "Legal", "Tabloid"
    landscape=False,
    print_background=True,
    margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
    scale=1.0,             # 0.1–2.0
    display_header_footer=False,
)
```

## Timeout handling

```python
from playwright.async_api import TimeoutError

try:
    await page.goto(url, timeout=15000)
except TimeoutError:
    pass  # capture partial content
screenshot = await page.screenshot(full_page=True)
```

## Memory limits

| Page height | Approx PNG size | Safe? |
|---|---|---|
| < 10,000 px | < 5 MB | Yes |
| 10,000–30,000 px | 10–25 MB | Yes (monitor RAM) |
| 30,000–50,000 px | 25–40 MB | Limit concurrency |
| > 50,000 px | > 40 MB | Reject, OOM risk |
