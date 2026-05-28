import asyncio
from urllib.parse import quote_plus
from agent.platforms.base import JobPlatform

class IndeedPlatform(JobPlatform):
    @property
    def name(self):
        return "Indeed"

    async def process_platform(self, keywords: str, locations: str):
        self.log(f"[{self.name}] Starting search: '{keywords}' in '{locations}'")

        q = quote_plus(keywords)
        loc = quote_plus(locations) if locations else "Germany"
        # jt=internship to filter for internships
        url = f"https://de.indeed.com/jobs?q={q}&l={loc}&jt=internship&sort=date"

        await self.browser.goto(url)
        await asyncio.sleep(4)

        page_text = await self.browser.get_page_text()

        # Indeed often throws a Cloudflare check — detect it and warn
        if "verify you are human" in page_text.lower() or "cf-browser-verification" in page_text.lower():
            self.log(f"[{self.name}] ⚠️ Blocked by Cloudflare/CAPTCHA. Skipping this cycle.", level="warning")
            return

        # Handle cookie consent
        elements = await self.browser.get_interactive_elements()
        for el in elements:
            label = el.get("label", "").lower()
            if "accept" in label or "akzeptieren" in label:
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
            self.log(f"[{self.name}] No matching jobs found on Indeed.")
            return

        self.log(f"[{self.name}] Found {len(jobs)} matching jobs. Processing...")

        for job in jobs[:3]:
            job_url = job.get("url", "")
            job_title = job.get("title", "Unknown Role")
            company = job.get("company", "Unknown Company")

            if not job_url:
                continue

            if not job_url.startswith("http"):
                job_url = f"https://de.indeed.com{job_url}"

            if self.is_already_applied(job_url):
                self.log(f"[{self.name}] Already applied to {job_title} @ {company}. Skipping.")
                continue

            self.log(f"[{self.name}] 🎯 Attempting to apply: {job_title} @ {company}")
            try:
                await self.run_application_loop(job_url, job_title, company)
            except Exception as e:
                self.log(f"[{self.name}] Application loop crashed for {job_title}: {e}", level="error")

            await asyncio.sleep(8)
