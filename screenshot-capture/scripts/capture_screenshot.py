"""
Full-page screenshot capture using Playwright.

Usage:
    python capture_screenshot.py https://example.com output.png
    python capture_screenshot.py https://example.com output.jpg --format jpeg --quality 80
    python capture_screenshot.py https://example.com output.png --mobile
    python capture_screenshot.py https://example.com element.png --selector ".chart"
"""

import asyncio
import argparse
from playwright.async_api import async_playwright


async def capture(
    url: str,
    output: str,
    format: str = "png",
    quality: int = 80,
    full_page: bool = True,
    width: int = 1920,
    height: int = 1080,
    mobile: bool = False,
    selector: str | None = None,
    wait_until: str = "networkidle",
    timeout: int = 30000,
    remove_selectors: list[str] | None = None,
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--disable-dev-shm-usage"],
        )

        viewport = {"width": 390, "height": 844} if mobile else {"width": width, "height": height}
        ctx = await browser.new_context(viewport=viewport)
        page = await ctx.new_page()

        try:
            print(f"[capture] Loading {url}...")
            await page.goto(url, wait_until=wait_until, timeout=timeout)

            # Remove floating elements
            if remove_selectors:
                for sel in remove_selectors:
                    await page.evaluate(f"""
                        document.querySelectorAll('{sel}').forEach(el => el.remove());
                    """)

            # Wait for fonts
            await page.evaluate("document.fonts.ready")

            if selector:
                print(f"[capture] Capturing element: {selector}")
                element = await page.wait_for_selector(selector, state="visible", timeout=timeout)
                await element.screenshot(path=output, type=format, quality=quality if format == "jpeg" else None)
            else:
                mode = "full-page" if full_page else "viewport"
                print(f"[capture] Capturing {mode} ({viewport['width']}x{viewport['height']})...")
                await page.screenshot(path=output, full_page=full_page, type=format, quality=quality if format == "jpeg" else None)

            print(f"[capture] Saved to {output}")
        finally:
            await ctx.close()
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description="Capture full-page screenshots with Playwright")
    parser.add_argument("url", help="URL to capture")
    parser.add_argument("output", help="Output file path")
    parser.add_argument("--format", choices=["png", "jpeg"], default="png")
    parser.add_argument("--quality", type=int, default=80, help="JPEG quality (1-100)")
    parser.add_argument("--viewport", action="store_false", dest="full_page", help="Viewport only (no full-page)")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--mobile", action="store_true", help="Use iPhone 14 viewport (390x844)")
    parser.add_argument("--selector", help="CSS selector to capture a single element")
    parser.add_argument("--timeout", type=int, default=30000, help="Page load timeout in ms")
    parser.add_argument("--remove", nargs="*", default=None, help="CSS selectors to remove before capture")
    args = parser.parse_args()
    asyncio.run(capture(
        url=args.url,
        output=args.output,
        format=args.format,
        quality=args.quality,
        full_page=args.full_page,
        width=args.width,
        height=args.height,
        mobile=args.mobile,
        selector=args.selector,
        timeout=args.timeout,
        remove_selectors=args.remove,
    ))


if __name__ == "__main__":
    main()
