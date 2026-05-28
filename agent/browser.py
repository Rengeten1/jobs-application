import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# playwright-stealth masks the headless browser's JS fingerprint
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

PROFILE_DIR = Path(__file__).parent.parent / "data" / "browser_profile"

class BrowserAgent:
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.context = None
        self.page = None

    async def start(self):
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self.playwright = await async_playwright().start()

        # Use a persistent context so cookies/login sessions are saved to disk.
        # This means once you log into LinkedIn manually, it stays logged in forever.
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
            ignore_default_args=["--enable-automation"],
        )
        self.page = await self.context.new_page()

        # Apply stealth patches to every new page to neutralize bot-detection heuristics
        if STEALTH_AVAILABLE:
            await stealth_async(self.page)

    async def new_page(self):
        """Open a fresh page within the same persistent context (same cookies)."""
        page = await self.context.new_page()
        if STEALTH_AVAILABLE:
            await stealth_async(page)
        return page

    async def close(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def goto(self, url, timeout=30000):
        await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        # Random human-like delay after navigation
        await asyncio.sleep(1.5 + (hash(url) % 3))

    async def get_page_text(self):
        return await self.page.inner_text("body")

    async def get_interactive_elements(self):
        """
        Inject a script to extract all visible, interactive elements and return
        them as a JSON list. Each element gets a unique `data-ai-id` attribute
        so the agent can reference it later with click/fill actions.
        """
        script = """
        () => {
            let elements = [];
            let idx = 0;
            document.querySelectorAll(
                'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [role="button"], [role="option"]'
            ).forEach((el) => {
                let rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.top < window.innerHeight * 2) {
                    el.setAttribute('data-ai-id', idx);
                    let label = (
                        el.innerText ||
                        el.getAttribute('aria-label') ||
                        el.getAttribute('placeholder') ||
                        el.getAttribute('value') ||
                        el.getAttribute('name') ||
                        el.getAttribute('type') ||
                        ''
                    ).trim().slice(0, 120);
                    
                    if (label) {
                        elements.push({
                            id: idx,
                            tag: el.tagName.toLowerCase(),
                            type: el.type || el.getAttribute('role') || '',
                            label: label,
                        });
                    }
                    idx++;
                }
            });
            return elements;
        }
        """
        return await self.page.evaluate(script)

    async def click_element(self, element_id, timeout=5000):
        try:
            locator = self.page.locator(f'[data-ai-id="{element_id}"]')
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.click()
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            # Fallback: try a JS click if the locator times out (useful for hidden elements)
            await self.page.evaluate(f'document.querySelector(\'[data-ai-id="{element_id}"]\').click()')

    async def fill_element(self, element_id, text, timeout=5000):
        locator = self.page.locator(f'[data-ai-id="{element_id}"]')
        await locator.wait_for(state="visible", timeout=timeout)
        await locator.fill(text)

    async def upload_file(self, element_id, file_path, timeout=5000):
        locator = self.page.locator(f'[data-ai-id="{element_id}"]')
        await locator.set_input_files(file_path, timeout=timeout)

    async def screenshot(self, path="debug_screenshot.png"):
        await self.page.screenshot(path=path, full_page=False)
