from playwright.async_api import async_playwright
import asyncio

class BrowserAgent:
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        # For Raspberry Pi, we might need to specify executable_path if standard installation fails, 
        # but playwright install should handle chromium.
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def goto(self, url):
        await self.page.goto(url, wait_until='domcontentloaded')

    async def get_interactive_elements(self):
        # Extract buttons, inputs, links to send to LLM
        # This is a simplified version of what browser-use does.
        script = """
        () => {
            let elements = [];
            document.querySelectorAll('button, input, select, textarea, a[href]').forEach((el, index) => {
                let rect = el.getBoundingClientRect();
                if(rect.width > 0 && rect.height > 0) {
                    el.setAttribute('data-ai-id', index);
                    elements.push({
                        id: index,
                        tag: el.tagName,
                        type: el.type || '',
                        text: el.innerText || el.value || el.placeholder || '',
                        name: el.name || '',
                        aria: el.getAttribute('aria-label') || ''
                    });
                }
            });
            return elements;
        }
        """
        return await self.page.evaluate(script)
    
    async def click_element(self, element_id):
        await self.page.click(f'[data-ai-id="{element_id}"]')

    async def fill_element(self, element_id, text):
        await self.page.fill(f'[data-ai-id="{element_id}"]', text)

    async def get_page_text(self):
        return await self.page.evaluate('document.body.innerText')
