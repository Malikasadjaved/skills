"""
FastAPI endpoint for full-page screenshot capture.

Usage:
    pip install playwright fastapi uvicorn[standard]
    playwright install chromium
    uvicorn fastapi_endpoint:app --reload

Endpoints:
    GET /screenshot?url=https://example.com           → PNG screenshot
    GET /screenshot?url=https://example.com&format=jpeg&quality=75 → JPEG
    GET /screenshot/element?url=https://example.com&selector=.chart → element capture
    GET /screenshot/pdf?url=https://example.com        → PDF
    GET /health                                        → health check
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from playwright.async_api import async_playwright, Browser


BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
SCREENSHOT_TIMEOUT = int(os.getenv("SCREENSHOT_TIMEOUT", "30000"))
MAX_HEIGHT = int(os.getenv("SCREENSHOT_MAX_HEIGHT", "40000"))
CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT", "5"))

_browser: Browser | None = None
_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _browser
    p = await async_playwright().start()
    _browser = await p.chromium.launch(
        headless=BROWSER_HEADLESS,
        args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    )
    print(f"[screenshot] Browser ready (headless={BROWSER_HEADLESS})")
    yield
    await _browser.close()
    await p.stop()
    print("[screenshot] Browser closed")


app = FastAPI(title="Screenshot API", version="1.0.0", lifespan=lifespan)

REMOVE_SELECTORS = ".cookie-banner, .cookie-consent, #intercom-container, .chat-widget"


@app.get("/screenshot")
async def screenshot(
    url: str = Query(..., description="URL to capture"),
    full_page: bool = Query(True),
    width: int = Query(1920, ge=320, le=3840),
    height: int = Query(1080, ge=240, le=2160),
    format: str = Query("png", pattern=r"^(png|jpeg)$"),
    quality: int = Query(80, ge=10, le=100),
):
    async with _semaphore:
        ctx = await _browser.new_context(viewport={"width": width, "height": height})
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=SCREENSHOT_TIMEOUT)

            # Guard against oversized pages
            page_height = await page.evaluate("document.body.scrollHeight")
            if page_height > MAX_HEIGHT:
                raise HTTPException(status_code=413, detail=f"Page too tall: {page_height}px (max {MAX_HEIGHT})")

            # Remove floating elements
            await page.evaluate(f"""document.querySelectorAll('{REMOVE_SELECTORS}').forEach(el => el.remove());""")
            await page.evaluate("document.fonts.ready")

            img = await page.screenshot(full_page=full_page, type=format, quality=quality if format == "jpeg" else None)
            mt = "image/png" if format == "png" else "image/jpeg"
            return Response(content=img, media_type=mt)
        finally:
            await ctx.close()


@app.get("/screenshot/element")
async def capture_element(
    url: str = Query(...),
    selector: str = Query(...),
    width: int = Query(1920),
    height: int = Query(1080),
):
    async with _semaphore:
        ctx = await _browser.new_context(viewport={"width": width, "height": height})
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=SCREENSHOT_TIMEOUT)
            element = await page.wait_for_selector(selector, state="visible", timeout=10000)
            img = await element.screenshot(type="png")
            return Response(content=img, media_type="image/png")
        finally:
            await ctx.close()


@app.get("/screenshot/pdf")
async def pdf(url: str = Query(...)):
    async with _semaphore:
        ctx = await _browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=SCREENSHOT_TIMEOUT)
            pdf_bytes = await page.pdf(format="A4", print_background=True)
            return Response(content=pdf_bytes, media_type="application/pdf")
        finally:
            await ctx.close()


@app.get("/health")
async def health():
    ok = _browser is not None and _browser.is_connected()
    return {"status": "ok" if ok else "degraded", "browser": str(ok)}
