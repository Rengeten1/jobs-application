from abc import ABC, abstractmethod
from pathlib import Path
from app.database import SessionLocal
from app.models import Job, Config

CV_PATH = str(Path(__file__).parent.parent.parent / "data" / "CV_V1.pdf")

class JobPlatform(ABC):
    def __init__(self, browser_agent, llm_client, log_activity, profile_data):
        self.browser = browser_agent
        self.llm = llm_client
        self.log = log_activity
        self.profile = profile_data

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    async def process_platform(self, keywords: str, locations: str):
        """Main entry point called by the orchestrator."""
        pass

    def save_job(self, title: str, company: str, url: str, status: str = "applied"):
        """Persist a job application record to the SQLite database."""
        try:
            with SessionLocal() as db:
                existing = db.query(Job).filter(Job.url == url).first()
                if existing:
                    return False  # Already applied
                job = Job(title=title, company=company, url=url, status=status)
                db.add(job)
                db.commit()
                return True
        except Exception as e:
            self.log(f"[{self.name}] Failed to save job to DB: {e}", level="error")
            return False

    def is_already_applied(self, url: str) -> bool:
        """Check if a job URL has already been saved to avoid re-applying."""
        with SessionLocal() as db:
            return db.query(Job).filter(Job.url == url).first() is not None

    async def run_application_loop(self, job_url: str, job_title: str, company: str, max_steps: int = 20):
        """
        The core agentic loop for filling out a single application form.
        The LLM observes the page state and decides what action to take next,
        looping until the form is submitted or the LLM gives up.
        """
        self.log(f"[{self.name}] Starting application loop for: {job_title} @ {company}")
        await self.browser.goto(job_url)

        for step in range(max_steps):
            elements = await self.browser.get_interactive_elements()
            page_text = await self.browser.get_page_text()

            action = await self.llm.decide_next_action(self.profile, elements, page_text)
            act = action.get("action", "done")

            self.log(f"[{self.name}] Step {step+1}: LLM decided → {act}")

            if act == "click":
                try:
                    await self.browser.click_element(action["id"])
                except Exception as e:
                    self.log(f"[{self.name}] Click failed on element {action.get('id')}: {e}", level="warning")

            elif act == "fill":
                try:
                    await self.browser.fill_element(action["id"], action.get("text", ""))
                except Exception as e:
                    self.log(f"[{self.name}] Fill failed on element {action.get('id')}: {e}", level="warning")

            elif act == "upload_cv":
                try:
                    # Find file input elements and upload the CV
                    file_inputs = [el for el in elements if el.get("type") == "file"]
                    if file_inputs:
                        await self.browser.upload_file(file_inputs[0]["id"], CV_PATH)
                        self.log(f"[{self.name}] CV uploaded successfully.")
                    else:
                        self.log(f"[{self.name}] No file input found for CV upload.", level="warning")
                except Exception as e:
                    self.log(f"[{self.name}] CV upload failed: {e}", level="error")

            elif act == "generate_cover_letter":
                self.log(f"[{self.name}] Generating tailored cover letter...")
                cover_letter = await self.llm.generate_cover_letter(self.profile, page_text[:2000])
                # Find the textarea and fill it
                text_areas = [el for el in elements if el.get("tag") in ("textarea",)]
                if text_areas:
                    await self.browser.fill_element(text_areas[0]["id"], cover_letter)
                    self.log(f"[{self.name}] Cover letter filled successfully.")
                else:
                    self.log(f"[{self.name}] No textarea found for cover letter.", level="warning")

            elif act == "done":
                reason = action.get("reason", "No reason given")
                if "submit" in reason.lower() or "success" in reason.lower() or "applied" in reason.lower():
                    self.log(f"[{self.name}] ✅ Application submitted for {job_title} @ {company}!")
                    self.save_job(job_title, company, job_url, status="applied")
                else:
                    self.log(f"[{self.name}] ⏩ Skipping {job_title}: {reason}")
                    self.save_job(job_title, company, job_url, status="skipped")
                return

            else:
                self.log(f"[{self.name}] Unknown action: {act}. Stopping this application.", level="warning")
                return

        self.log(f"[{self.name}] Max steps reached for {job_title}. Giving up.", level="warning")
        self.save_job(job_title, company, job_url, status="failed")
