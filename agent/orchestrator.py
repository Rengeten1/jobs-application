import os
import asyncio
import logging
from app.database import SessionLocal
from app.models import Config
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

    async def start(self):
        if self.running:
            return
        
        api_key = os.getenv("GITHUB_API_KEY")
        if not api_key:
            logger.error("No GitHub API key configured in .env.")
            return

        self.llm_client = LLMClient(api_key)
        self.browser_agent = BrowserAgent(headless=True)
        await self.browser_agent.start()
        self.running = True
        
        # Start the main loop in the background
        asyncio.create_task(self.run_loop())
        logger.info("Agent started successfully.")

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
                
                logger.info(f"Searching for: {keywords}")
                logger.info(f"Loaded profile: {profile_info[:50]}...")
                
                # Here would be the logic to go to LinkedIn/Indeed and search.
                # For this MVP, we simulate landing on an application page.
                # Real implementation would have a search scraper loop here.
                
                # Mock example of interacting with a page:
                # await self.browser_agent.goto("https://example.com/apply")
                # elements = await self.browser_agent.get_interactive_elements()
                # page_text = await self.browser_agent.get_page_text()
                # next_action = await self.llm_client.decide_next_action(profile_info, elements, page_text)
                
                # Execute action logic...
                
                logger.info("Sleeping for 60 seconds before next check...")
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(60)

# Global orchestrator instance
orchestrator = AgentOrchestrator()
