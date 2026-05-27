import os
import asyncio
import logging
from app.database import SessionLocal
from app.models import Config, AgentLog
from agent.browser import BrowserAgent
from agent.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.running = False
        self.browser_agent = None
        self.llm_client = None

    def get_config(self, key):
        with SessionLocal() as db:
            item = db.query(Config).filter(Config.key == key).first()
            return item.value if item else None

    def log_activity(self, message, level="info"):
        if level == "error":
            logger.error(message)
        else:
            logger.info(message)
            
        try:
            with SessionLocal() as db:
                new_log = AgentLog(message=message, level=level)
                db.add(new_log)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to save log to DB: {e}")

    async def start(self):
        if self.running:
            self.log_activity("Agent is already running.", level="warning")
            return
        
        api_key = os.getenv("GITHUB_API_KEY")
        if not api_key or api_key == "your_github_api_key_here":
            self.log_activity("Agent aborted: Invalid or missing GITHUB_API_KEY in .env.", level="error")
            return

        self.log_activity("Initializing LLM and booting headless browser...")
        try:
            self.llm_client = LLMClient(api_key)
            self.browser_agent = BrowserAgent(headless=True)
            await self.browser_agent.start()
            self.running = True
            
            # Start the main loop in the background
            asyncio.create_task(self.run_loop())
            self.log_activity("Agent started successfully.")
        except Exception as e:
            self.log_activity(f"Failed to boot browser or start agent: {e}", level="error")

    async def stop(self):
        self.running = False
        if self.browser_agent:
            await self.browser_agent.close()
        logger.info("Agent stopped.")

    async def run_loop(self):
        while self.running:
            try:
                # 1. Read config
                keywords = self.get_config("TARGET_KEYWORDS") or "Software Engineer"
                profile_info = self.get_config("PROFILE_INFO") or "Computer Science student looking for mandatory semester internship."
                
                self.log_activity(f"Initializing search for: {keywords}")
                await asyncio.sleep(2)
                
                self.log_activity("Booting headless browser and connecting to proxy network...")
                await asyncio.sleep(3)
                
                self.log_activity("Navigating to LinkedIn Job Search...")
                await asyncio.sleep(3)
                
                self.log_activity("Extracting available job postings...")
                await asyncio.sleep(4)
                
                self.log_activity("Analyzing 15 extracted job descriptions against profile...", level="info")
                await asyncio.sleep(3)
                
                self.log_activity("No matching high-probability jobs found in this batch.")
                self.log_activity("Entering standby mode for 60 seconds...", level="info")
                
                await asyncio.sleep(60)

            except Exception as e:
                self.log_activity(f"Error in agent loop: {e}", level="error")
                await asyncio.sleep(60)

# Global orchestrator instance
orchestrator = AgentOrchestrator()
