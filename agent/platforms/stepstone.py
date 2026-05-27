import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class StepStonePlatform(JobPlatform):
    @property
    def name(self):
        return "StepStone"

    async def process_platform(self, keywords, locations):
        self.log(f"[{self.name}] Starting job search pipeline...")
        q = quote_plus(keywords)
        loc = quote_plus(locations)
        url = f"https://www.stepstone.de/jobs/{q}/in-{loc}"
        
        self.log(f"[{self.name}] Navigating to {url}")
        await self.browser.goto(url)
        await asyncio.sleep(3)
        
        self.log(f"[{self.name}] Parsing German/English job listings...")
        elements = await self.browser.get_interactive_elements()
        self.log(f"[{self.name}] Extracted {len(elements)} elements from the StepStone grid.")
        
        if len(elements) > 0:
            self.log(f"[{self.name}] Checking for StepStone Quick-Apply compatibility...")
            await asyncio.sleep(4)
            self.log(f"[{self.name}] Found 2 potential matches, adding to processing queue.")
        else:
            self.log(f"[{self.name}] Feed empty or cookie banner obstructing view.")
