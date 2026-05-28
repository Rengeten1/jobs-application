import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class StepStonePlatform(JobPlatform):
    @property
    def name(self):
        return "StepStone"

    async def process_platform(self, keywords: str, locations: str):
        self.log(f"[{self.name}] Starting search: '{keywords}' in '{locations}'")

        q = quote_plus(keywords)
        loc = quote_plus(locations) if locations else "germany"
        url = f"https://www.stepstone.de/jobs/{q}/in-{loc}?what={q}&where={loc}&radius=30&resultsPerPage=20"

        await self.browser.goto(url)
        await asyncio.sleep(3)

        # Handle cookie consent if present
        page_text = await self.browser.get_page_text()
        elements = await self.browser.get_interactive_elements()
        
        # Look for cookie accept button
        for el in elements:
            label = el.get("label", "").lower()
            if "accept" in label or "akzeptieren" in label or "alle akzeptieren" in label:
                self.log(f"[{self.name}] Accepting cookie consent...")
                try:
                    await self.browser.click_element(el["id"])
                    await asyncio.sleep(2)
                except Exception:
                    pass
                break

        page_text = await self.browser.get_page_text()
        self.log(f"[{self.name}] Asking LLM to identify matching jobs...")
        jobs = await self.llm.find_matching_jobs(self.profile, keywords, page_text)

        if not jobs:
            self.log(f"[{self.name}] No matching jobs found on StepStone for these keywords.")
            return

        self.log(f"[{self.name}] Found {len(jobs)} matching jobs. Processing...")

        for job in jobs[:3]:
            job_url = job.get("url", "")
            job_title = job.get("title", "Unknown Role")
            company = job.get("company", "Unknown Company")

            if not job_url:
                continue

            # Ensure URL is absolute
            if not job_url.startswith("http"):
                job_url = f"https://www.stepstone.de{job_url}"

            if self.is_already_applied(job_url):
                self.log(f"[{self.name}] Already applied to {job_title} @ {company}. Skipping.")
                continue

            self.log(f"[{self.name}] 🎯 Attempting to apply: {job_title} @ {company}")
            try:
                await self.run_application_loop(job_url, job_title, company)
            except Exception as e:
                self.log(f"[{self.name}] Application loop crashed for {job_title}: {e}", level="error")

            await asyncio.sleep(8)
