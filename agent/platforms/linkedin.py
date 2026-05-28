import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class LinkedInPlatform(JobPlatform):
    @property
    def name(self):
        return "LinkedIn"

    async def process_platform(self, keywords: str, locations: str):
        self.log(f"[{self.name}] Starting search: '{keywords}' in '{locations}'")

        q = quote_plus(keywords)
        loc = quote_plus(locations) if locations else ""
        # f=TPF filters for Easy Apply jobs only
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}&f_TPF=1&f_JT=I"
        
        await self.browser.goto(url)
        await asyncio.sleep(3)

        # Check if we landed on a login wall
        page_text = await self.browser.get_page_text()
        if "join now" in page_text.lower() or "sign in" in page_text.lower() and "jobs" not in page_text.lower():
            self.log(f"[{self.name}] ⚠️ Hit login wall. The browser profile may need initial manual login. Skipping.", level="warning")
            return

        self.log(f"[{self.name}] Asking LLM to find matching internship jobs on this page...")
        jobs = await self.llm.find_matching_jobs(self.profile, keywords, page_text)

        if not jobs:
            self.log(f"[{self.name}] No matching jobs found on current search page.")
            return

        self.log(f"[{self.name}] Found {len(jobs)} matching jobs. Processing one by one...")

        for job in jobs[:3]:  # Process max 3 per cycle to avoid rate limits
            job_url = job.get("url", "")
            job_title = job.get("title", "Unknown Role")
            company = job.get("company", "Unknown Company")

            if not job_url:
                continue

            if self.is_already_applied(job_url):
                self.log(f"[{self.name}] Already applied to {job_title} @ {company}. Skipping.")
                continue

            self.log(f"[{self.name}] 🎯 Attempting to apply: {job_title} @ {company}")
            try:
                await self.run_application_loop(job_url, job_title, company)
            except Exception as e:
                self.log(f"[{self.name}] Application loop crashed for {job_title}: {e}", level="error")

            # Human-like pause between applications
            await asyncio.sleep(8)
