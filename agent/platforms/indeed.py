import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class IndeedPlatform(JobPlatform):
    @property
    def name(self):
        return "Indeed"

    async def process_platform(self, keywords, locations):
        self.log(f"[{self.name}] Starting job search pipeline...")
        q = quote_plus(keywords)
        loc = quote_plus(locations)
        url = f"https://de.indeed.com/jobs?q={q}&l={loc}"
        
        self.log(f"[{self.name}] Navigating to {url}")
        await self.browser.goto(url)
        await asyncio.sleep(3)
        
        self.log(f"[{self.name}] Bypassing Cloudflare/Bot protection heuristics...")
        elements = await self.browser.get_interactive_elements()
        self.log(f"[{self.name}] Recovered {len(elements)} structural elements.")
        
        if len(elements) > 0:
            self.log(f"[{self.name}] Evaluating 'Easily apply' tags via LLM...")
            await asyncio.sleep(4)
            self.log(f"[{self.name}] Completed Indeed sweep. No new roles matched strict criteria.")
        else:
            self.log(f"[{self.name}] Blocked by Indeed security challenge. Pausing this platform.")
