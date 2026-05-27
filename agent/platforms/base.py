from abc import ABC, abstractmethod

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
    async def process_platform(self, keywords, locations):
        """Main method called by orchestrator. Should handle navigation, search, and applying."""
        pass
