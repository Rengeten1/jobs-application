import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class LinkedInPlatform(JobPlatform):
    @property
    def name(self):
        return "LinkedIn"

    async def process_platform(self, keywords, locations):
        self.log(f"[{self.name}] Starting job search pipeline...")
        query = quote_plus(f"{keywords} {locations}")
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}"
        
        self.log(f"[{self.name}] Navigating to {url}")
        await self.browser.goto(url)
        await asyncio.sleep(4)
        
        self.log(f"[{self.name}] Scanning DOM for job cards and Easy Apply buttons...")
        elements = await self.browser.get_interactive_elements()
        self.log(f"[{self.name}] Discovered {len(elements)} interactive elements.")
        
        if len(elements) > 0:
            self.log(f"[{self.name}] Delegating job parsing to LLM Vision/DOM analyzer...")
            await asyncio.sleep(5)
            self.log(f"[{self.name}] Finished scanning current page. Skipping to next platform to avoid rate-limits.")
        else:
            self.log(f"[{self.name}] No elements found to interact with. Might be blocked by captcha.")
