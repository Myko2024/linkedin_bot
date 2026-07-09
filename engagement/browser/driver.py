"""Generic Playwright wrapper: find elements, click, scroll, evaluate, tabs.

Knows nothing about LinkedIn -- it's just "how to drive a browser". Everything
site-specific (selectors, what a Like means) lives in linkedin.py. Locators are
returned to callers so they can be re-used across find/attr/click on the same
element; all interaction primitives swallow Playwright errors and report a simple
bool / None so callers don't have to sprinkle try/except everywhere.
"""
from __future__ import annotations

import asyncio
import random

from playwright.async_api import (
    Error as PWError,
    Locator,
    TimeoutError as PWTimeout,
    async_playwright,
)


class Browser:
    def __init__(self, user_data_dir: str, *, headless: bool = False,
                 locale: str = "en-US", viewport: tuple[int, int] = (1366, 860)):
        self._user_data_dir = user_data_dir
        self._headless = headless
        self._locale = locale
        self._viewport = viewport
        self._pw = None
        self.ctx = None
        self.page = None

    # -- lifecycle (async context manager) ---------------------------------- #

    async def __aenter__(self) -> "Browser":
        self._pw = await async_playwright().start()
        self.ctx = await self._pw.chromium.launch_persistent_context(
            self._user_data_dir,
            headless=self._headless,   # headless Chromium is flagged almost instantly
            viewport={"width": self._viewport[0], "height": self._viewport[1]},
            locale=self._locale,       # force English -- selectors use English aria-labels
            extra_http_headers={"Accept-Language": f"{self._locale},en;q=0.9"},
            args=["--disable-blink-features=AutomationControlled", f"--lang={self._locale}"],
        )
        self.page = await self.ctx.new_page()
        for p in self.ctx.pages:
            if p is not self.page:
                await p.close()
        return self

    async def __aexit__(self, *exc) -> None:
        if self.ctx:
            await self.ctx.close()
        if self._pw:
            await self._pw.stop()

    # -- timing ------------------------------------------------------------- #

    async def pause(self, a: float = 1.2, b: float = 3.2) -> None:
        """Randomised delay. Constant-interval clicking trips bot detection."""
        await asyncio.sleep(random.uniform(a, b))

    # -- navigation --------------------------------------------------------- #

    @property
    def url(self) -> str:
        return self.page.url

    async def goto(self, url: str, wait_until: str = "domcontentloaded",
                   timeout: int = 30_000) -> None:
        await self.page.goto(url, wait_until=wait_until, timeout=timeout)

    async def wait_for(self, selector: str, timeout: int = 12_000) -> bool:
        """Wait for any element matching `selector`; return whether it appeared."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except (PWTimeout, PWError):
            return False

    # -- finding / reading -------------------------------------------------- #

    async def count(self, selector: str) -> int:
        return await self.page.locator(selector).count()

    async def find_all(self, selector: str) -> list[Locator]:
        """Snapshot the currently-matching elements as individual locators."""
        loc = self.page.locator(selector)
        return [loc.nth(i) for i in range(await loc.count())]

    async def eval_on(self, locator: Locator, js: str):
        """Run `js(element)` on one element; None on failure."""
        try:
            return await locator.evaluate(js)
        except (PWTimeout, PWError):
            return None

    async def attr(self, locator: Locator, name: str) -> str | None:
        try:
            return await locator.get_attribute(name)
        except (PWTimeout, PWError):
            return None

    async def is_visible(self, locator: Locator) -> bool:
        try:
            return await locator.is_visible()
        except (PWTimeout, PWError):
            return False

    # -- interaction -------------------------------------------------------- #

    async def click(self, locator: Locator, timeout: int = 4_000) -> bool:
        """Real, actionable click. Returns False (rather than raising) when the
        element isn't clickable right now -- off-screen, covered by an overlay, or
        detached by virtualization -- so the caller can retry it later. Centres
        the element first so it isn't behind the sticky nav / messaging widget."""
        try:
            if not await locator.is_visible():
                return False
            await locator.evaluate("el => el.scrollIntoView({block: 'center'})")
            await self.pause(0.3, 0.7)
            await locator.click(timeout=timeout)
            return True
        except (PWTimeout, PWError):
            return False

    async def scroll_to_top(self) -> None:
        await self.page.evaluate("window.scrollTo(0, 0)")

    async def scroll_step(self, fraction: float = 0.9) -> None:
        await self.page.evaluate(
            f"window.scrollBy(0, Math.round(document.documentElement.clientHeight * {fraction}))"
        )

    # -- throwaway tab (e.g. a profile visit) ------------------------------- #

    async def scrape_tab(self, url: str, js: str, timeout: int = 20_000,
                         settle: tuple[float, float] = (1.5, 2.5)):
        """Open `url` in a fresh tab, run `js()`, return its result, close the tab.
        Returns None if the page fails to load."""
        page = await self.ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await self.pause(*settle)
            return await page.evaluate(js)
        except (PWTimeout, PWError):
            return None
        finally:
            await page.close()
