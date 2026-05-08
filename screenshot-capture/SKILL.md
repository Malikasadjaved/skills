---
name: screenshot-capture
description: >
  Use this skill when capturing full-page screenshots of webpages —
  Playwright headless browser, full-page PNG/JPEG output, lazy-load
  handling, element-specific captures, PDF generation, device
  emulation (mobile/tablet), and FastAPI integration for agent
  backends. Covers Docker deployment with Chromium dependencies.
triggers:
  - screenshot
  - full page screenshot
  - web capture
  - page to image
  - playwright
  - puppeteer
  - browser screenshot
  - webpage snapshot
  - capture webpage
  - headless browser
  - website screenshot
  - page to png
  - web page to pdf
version: 1.0.0
author: malikasadjaved
---

## Overview

Capture full-page, viewport, and element-specific screenshots of any webpage
using Playwright's headless Chromium. This skill covers the full application-layer:
from one-off scripts through FastAPI endpoints serving AI agents.

**What this skill covers (that generic Playwright docs don't):**

- Full-page screenshots with lazy-load and infinite-scroll handling
- Production FastAPI endpoint — accept a URL, return a PNG
- Docker Compose with Chromium and all system dependencies
- Browser pooling so you don't launch a new browser per request
- Auth handling (cookies, headers, login-before-capture)
- PDF generation alongside PNG output
- Mobile and tablet device emulation
- Error handling for timeouts, oversized pages, auth walls, and dead URLs

**When to use this skill vs. other approaches:**

| Scenario | Use |
|---|---|
| I need to capture a full webpage as PNG from a URL | **This skill** |
| I need a FastAPI endpoint that returns screenshots | **This skill** |
| I want to write Playwright tests | Official Playwright docs |
| I need a general-purpose browser agent | agent-browser skill |
| I need to scrape structured data | firecrawl skill |

## Quick Start

### One-shot script (no server)

```python
import asyncio
from playwright.async_api import async_playwright

async def capture(url: str, output: str = "screenshot.png"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(url, wait_until="networkidle")
        await page.screenshot(path=output, full_page=True)
        await browser.close()

asyncio.run(capture("https://example.com"))
```

This works but is NOT suitable for production — it launches a browser per
request (~500ms overhead), doesn't handle errors, and has no concurrency
control. The patterns below fix all of that.

## Full-Page Screenshot

### Basic full-page

```python
page = await browser.new_page()
await page.goto(url, wait_until="networkidle")
await page.screenshot(path="full.png", full_page=True)
```

`full_page=True` captures the entire scrollable page, not just the viewport.
The page must have finished loading and layout — `wait_until="networkidle"`
ensures lazy images and async content have loaded before capture.

### Viewport-only (no full_page)

```python
await page.set_viewport_size({"width": 1920, "height": 1080})
await page.screenshot(path="viewport.png")  # full_page defaults to False
```

### Custom viewport for specific breakpoints

```python
await page.set_viewport_size({"width": 390, "height": 844})   # iPhone 14
await page.screenshot(path="mobile.png", full_page=True)

await page.set_viewport_size({"width": 1024, "height": 768})  # iPad
await page.screenshot(path="tablet.png", full_page=True)
```

### JPEG for smaller file size

```python
await page.screenshot(
    path="page.jpg",
    full_page=True,
    type="jpeg",
    quality=80,           # 0-100, lower = smaller file
)
```

JPEG with quality 70–85 is 5-10x smaller than PNG for photo-heavy pages.
Use PNG when you need pixel-perfect text or transparency.

## Handling Lazy-Loaded Content

Many modern sites lazy-load images, videos, and content as the user scrolls.
`full_page=True` only captures what's rendered — if content hasn't loaded yet,
it captures empty placeholders.

### Scroll-to-trigger pattern

```python
import asyncio

async def scroll_to_load(page, max_scrolls: int = 20):
    """Scroll through the page to trigger lazy loading."""
    prev_height = await page.evaluate("document.body.scrollHeight")

    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)  # wait for lazy content to load
        await page.wait_for_load_state("networkidle")

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == prev_height:
            break  # no more content loaded
        prev_height = new_height

    await page.evaluate("window.scrollTo(0, 0)")  # scroll back to top
```

Call this BEFORE `page.screenshot(full_page=True)`. The page height stops
growing when all lazy content has been triggered.

### Infinite scroll pages

For true infinite-scroll feeds (Twitter, Reddit), set a reasonable limit:

```python
async def scroll_for_infinite_feed(page, max_items: int = 50):
    items = []
    while len(items) < max_items:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await page.wait_for_load_state("networkidle")
        items = await page.query_selector_all("[data-item]")  # adjust selector
    await page.evaluate("window.scrollTo(0, 0)")
```

Infinite scroll pages can produce enormous screenshots (50,000+ px tall).
Set a hard limit on scroll iterations or total screenshot height.

### Wait for specific element

```python
# Wait for a lazy-loaded hero image or component
await page.wait_for_selector("img.hero", state="visible", timeout=10000)
await page.screenshot(path="page.png", full_page=True)
```

More reliable than `networkidle` alone when you know exactly what must be loaded.

## Element-Specific Screenshots

### Capture a single element

```python
element = await page.query_selector("div.chart-container")
await element.screenshot(path="chart.png")
```

Captures only that element's bounding box — useful for charts, tables, modals.

### Capture with padding

```python
element = await page.query_selector("section.pricing")
box = await element.bounding_box()
await page.screenshot(
    path="pricing.png",
    clip={
        "x": box["x"] - 10,
        "y": box["y"] - 10,
        "width": box["width"] + 20,
        "height": box["height"] + 20,
    },
)
```

### Hide a fixed/floating element before capture

```python
# Remove cookie banners, chat widgets, sticky headers
await page.evaluate("""
    const elements = document.querySelectorAll('.cookie-banner, #chat-widget');
    elements.forEach(el => el.remove());
""")
await page.screenshot(path="clean.png", full_page=True)
```

Common selectors to remove: `.cookie-banner`, `#intercom-container`,
`.fixed-header`, `[data-testid="floating-action"]`.

## PDF Generation

### Full page to PDF

```python
await page.pdf(
    path="page.pdf",
    format="A4",
    print_background=True,      # include CSS backgrounds
    margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
)
```

### Custom page size

```python
await page.pdf(
    path="page.pdf",
    width="1920px",
    height="1080px",
    print_background=True,
)
```

### Landscape PDF

```python
await page.pdf(
    path="landscape.pdf",
    format="A4",
    landscape=True,
    print_background=True,
)
```

PDF output uses the print CSS of the page (@media print rules). Results differ
from screenshots — use PDF for documents and reports, PNG for visual parity.

## Device Emulation

Playwright ships with device descriptors for iPhone, iPad, Pixel, and more.

```python
from playwright.async_api import async_playwright, devices

iPhone = devices["iPhone 14 Pro"]
Pixel = devices["Pixel 7"]

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)

    # Mobile screenshot
    ctx = await browser.new_context(**iPhone)
    page = await ctx.new_page()
    await page.goto(url)
    await page.screenshot(path="iphone.png", full_page=True)
    await ctx.close()

    # Desktop screenshot
    ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await ctx.new_page()
    await page.goto(url)
    await page.screenshot(path="desktop.png", full_page=True)
    await ctx.close()
```

Available devices: `iPhone 14 Pro`, `iPhone 14 Pro Max`, `iPhone SE`,
`Pixel 7`, `iPad Pro`, `iPad Mini`, `Galaxy Tab S4`, and ~50 more.
Import from `playwright.async_api` → `devices` dict.

## Browser Pooling (Production)

Launching a browser per request adds ~500ms and leaks memory under load.
Pool a single browser instance and reuse contexts.

```python
import asyncio
from playwright.async_api import async_playwright, Browser

_browser: Browser | None = None
_lock = asyncio.Lock()

async def get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        async with _lock:
            if _browser is None or not _browser.is_connected():
                p = await async_playwright().start()
                _browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",           # required in Docker
                        "--disable-setuid-sandbox",
                    ],
                )
    return _browser

async def capture_screenshot(url: str) -> bytes:
    browser = await get_browser()
    ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        screenshot = await page.screenshot(full_page=True, type="png")
        return screenshot
    finally:
        await ctx.close()  # clean up this request's context, not the browser
```

Key points:
- **One browser, many contexts** — `new_context()` is cheap (~5ms), `launch()` is expensive (~500ms)
- **Each context is isolated** — cookies, localStorage, and session data don't leak between requests
- **`--no-sandbox`** required when running as root (Docker containers)
- **`--disable-dev-shm-usage`** prevents crashes in Docker where `/dev/shm` is small

## FastAPI Integration

### Full endpoint (accept URL, return screenshot)

```python
import io
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from playwright.async_api import async_playwright, Browser

app = FastAPI(title="Screenshot API")
_browser: Browser | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _browser
    p = await async_playwright().start()
    _browser = await p.chromium.launch(
        headless=True,
        args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    yield
    await _browser.close()
    await p.stop()

app = FastAPI(lifespan=lifespan)


@app.get("/screenshot")
async def capture(
    url: str = Query(..., description="URL to capture"),
    full_page: bool = Query(True, description="Capture full scrollable page"),
    width: int = Query(1920, ge=320, le=3840),
    height: int = Query(1080, ge=240, le=2160),
    format: str = Query("png", pattern=r"^(png|jpeg)$"),
    quality: int = Query(80, ge=10, le=100),
):
    ctx = await _browser.new_context(viewport={"width": width, "height": height})
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        screenshot = await page.screenshot(
            full_page=full_page,
            type=format,
            quality=quality if format == "jpeg" else None,
        )
        media_type = "image/png" if format == "png" else "image/jpeg"
        return Response(content=screenshot, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot failed: {e}")
    finally:
        await ctx.close()


@app.get("/screenshot/element")
async def capture_element(
    url: str = Query(...),
    selector: str = Query(..., description="CSS selector of the element"),
    width: int = Query(1920),
    height: int = Query(1080),
):
    ctx = await _browser.new_context(viewport={"width": width, "height": height})
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        element = await page.wait_for_selector(selector, state="visible", timeout=10000)
        screenshot = await element.screenshot(type="png")
        return Response(content=screenshot, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Element capture failed: {e}")
    finally:
        await ctx.close()


@app.get("/screenshot/pdf")
async def capture_pdf(url: str = Query(...)):
    ctx = await _browser.new_context()
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        pdf = await page.pdf(format="A4", print_background=True)
        return Response(content=pdf, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    finally:
        await ctx.close()


@app.get("/health")
async def health():
    return {"status": "ok" if _browser and _browser.is_connected() else "degraded"}
```

Rate-limit this endpoint. A single browser can handle ~5 concurrent screenshots
before memory becomes an issue. For higher throughput, launch multiple browser
instances behind a semaphore.

### Concurrency guard

```python
import asyncio

_semaphore = asyncio.Semaphore(5)  # max 5 concurrent captures

@app.get("/screenshot")
async def capture(url: str = Query(...)):
    async with _semaphore:
        ctx = await _browser.new_context()
        try:
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            screenshot = await page.screenshot(full_page=True)
            return Response(content=screenshot, media_type="image/png")
        finally:
            await ctx.close()
```

## Auth Handling

### Set cookies before capture

```python
ctx = await browser.new_context()
await ctx.add_cookies([
    {
        "name": "session",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/",
        "httpOnly": True,
        "secure": True,
    },
])
page = await ctx.new_page()
await page.goto("https://app.example.com/dashboard")
await page.screenshot(path="dashboard.png", full_page=True)
```

### Set auth header

```python
ctx = await browser.new_context(
    extra_http_headers={"Authorization": "Bearer your-token-here"},
)
page = await ctx.new_page()
await page.goto(url)
```

### Login-then-capture

```python
page = await ctx.new_page()

# Log in
await page.goto("https://example.com/login")
await page.fill("input[name='email']", "user@example.com")
await page.fill("input[name='password']", "password")
await page.click("button[type='submit']")
await page.wait_for_url("**/dashboard")  # confirm login succeeded

# Now capture the authenticated page
await page.goto("https://example.com/admin/reports")
await page.screenshot(path="report.png", full_page=True)
```

For production, store credentials in env vars and never log them.

## Error Handling

### Timeout

```python
from playwright.async_api import TimeoutError as PlaywrightTimeout

try:
    await page.goto(url, wait_until="networkidle", timeout=15000)
except PlaywrightTimeout:
    # Page is too slow — capture what we have
    await page.screenshot(path="partial.png", full_page=True)
```

### Navigation failure

```python
try:
    response = await page.goto(url, wait_until="networkidle", timeout=20000)
    if response and response.status >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Target returned {response.status}",
        )
except Exception as e:
    if "net::ERR_NAME_NOT_RESOLVED" in str(e):
        raise HTTPException(status_code=400, detail="Invalid URL or domain not found")
    if "net::ERR_CONNECTION_REFUSED" in str(e):
        raise HTTPException(status_code=502, detail="Target server refused connection")
    raise
```

### Oversized page guard

```python
MAX_HEIGHT = 40000  # ~40,000px — anything more will likely OOM

page = await ctx.new_page()
await page.goto(url)
height = await page.evaluate("document.body.scrollHeight")

if height > MAX_HEIGHT:
    raise HTTPException(
        status_code=413,
        detail=f"Page too tall ({height}px). Max is {MAX_HEIGHT}px.",
    )

await page.screenshot(path="page.png", full_page=True)
```

Infinite-scroll feeds can produce 100,000+ px pages — always guard against this.

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    chromium \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PLAYWRIGHT_BROWSERS_PATH=/usr/lib/chromium
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### docker-compose.yml

```yaml
services:
  screenshot:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G     # Chromium needs ~500MB minimum
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### requirements.txt

```
fastapi>=0.111.0
playwright>=1.40.0
uvicorn[standard]
```

## Environment Variables

```bash
BROWSER_HEADLESS=true        # Run headless (default: true)
SCREENSHOT_TIMEOUT=30000     # Page load timeout in ms (default: 30000)
SCREENSHOT_MAX_HEIGHT=40000  # Max page height in px (default: 40000)
CONCURRENCY_LIMIT=5          # Max concurrent captures (default: 5)
DEFAULT_VIEWPORT_WIDTH=1920  # Default viewport width (default: 1920)
DEFAULT_VIEWPORT_HEIGHT=1080 # Default viewport height (default: 1080)
```

Load with pydantic-settings:

```python
from pydantic_settings import BaseSettings

class ScreenshotSettings(BaseSettings):
    browser_headless: bool = True
    screenshot_timeout: int = 30000
    screenshot_max_height: int = 40000
    concurrency_limit: int = 5
    default_viewport_width: int = 1920
    default_viewport_height: int = 1080

    model_config = {"env_file": ".env"}
```

## Common Pitfalls

1. **Launching a browser per request.** A Chromium launch takes ~400–700ms and
   allocates ~200MB RAM. Pool one browser and create isolated contexts per request.

2. **No timeout on `page.goto()`.** Slow or dead pages will hang your endpoint
   indefinitely. Always set `timeout=` (in milliseconds). Default is 30000 — tune
   it for your use case.

3. **Capturing before content loads.** `wait_until="load"` only waits for the
   initial HTML — images, fonts, and async JS are still loading. Use
   `wait_until="networkidle"` for full rendering. For SPAs, add an explicit
   `wait_for_selector` on the root component.

4. **Forgetting `--no-sandbox` in Docker.** Chromium requires sandboxing unless
   running as root (Docker default). The flag is required in containers.

5. **No height limit on infinite-scroll pages.** Twitter, Reddit, and feed-based
   pages can generate 100,000+ px screenshots that OOM your server. Always cap.

6. **Web fonts not rendered.** If the page uses custom fonts, they may not load
   on first capture. Wait for `document.fonts.ready`:
   ```python
   await page.evaluate("document.fonts.ready")
   ```

7. **3rd-party embeds blocking load.** YouTube iframes, analytics scripts, and
   ad networks can prevent `networkidle`. Block them:
   ```python
   await page.route("**/*", lambda route: route.abort()
       if route.request.resource_type in ["media", "ping", "font"]
       else route.continue_())
   ```

8. **Not cleaning up browser contexts.** After each request, close the context
   (NOT the browser). Leaked contexts accumulate memory until the process dies.

## Install

```bash
pip install playwright>=1.40.0 fastapi uvicorn[standard]
playwright install chromium
```
