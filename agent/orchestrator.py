import os
import asyncio
import logging
from app.database import SessionLocal
from app.models import Config, AgentLog
from agent.browser import BrowserAgent
from agent.llm_client import LLMClient
from agent.platforms.linkedin import LinkedInPlatform
from agent.platforms.stepstone import StepStonePlatform
from agent.platforms.indeed import IndeedPlatform

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
        try:
            # 1. Read config
            keywords = self.get_config("TARGET_KEYWORDS") or "Software Engineer"
            profile_info = self.get_config("PROFILE_INFO") or "Computer Science student looking for mandatory semester internship."

            # Initialize platform plugins
            platforms = [
                LinkedInPlatform(self.browser_agent, self.llm_client, self.log_activity, profile_info),
                StepStonePlatform(self.browser_agent, self.llm_client, self.log_activity, profile_info),
                IndeedPlatform(self.browser_agent, self.llm_client, self.log_activity, profile_info)
            ]

            self.log_activity(f"Agent awake. Starting cross-platform search for: {keywords}")

            while self.running:
                for platform in platforms:
                    if not self.running:
                        break
                        
                    self.log_activity(f"--- Switching Context: {platform.name} ---")
                    try:
                        await platform.process_platform(keywords, keywords) # Using keywords for locations temporarily unless loc is specified
                    except Exception as e:
                        self.log_activity(f"Error processing {platform.name}: {e}", level="error")
                    
                    self.log_activity(f"Resting for 15 seconds to simulate human behavior and avoid rate limits...")
                    await asyncio.sleep(15)
                    
                self.log_activity("Completed full cycle of all platforms. Sleeping for 2 minutes before next sweep.")
                await asyncio.sleep(120)
                
        except Exception as e:
            self.log_activity(f"Agent encountered fatal error in loop: {e}", level="error")
            self.running = False

# Global orchestrator instance
orchestrator = AgentOrchestrator()
