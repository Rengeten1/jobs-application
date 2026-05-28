import json
import asyncio
from openai import AsyncOpenAI
from agent.prompts import SYSTEM_PROMPT_AGENT, JOB_SEARCH_PROMPT, COVER_LETTER_PROMPT

class LLMClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
        self.model = "gpt-4o-mini"

    async def _call(self, prompt: str, json_mode: bool = True, retries: int = 3) -> str:
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        for attempt in range(retries):
            try:
                response = await self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.2,
                    **kwargs
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise e

    async def decide_next_action(self, profile_info: str, elements: list, page_text: str) -> dict:
        """
        Given the current page state, ask the LLM what the agent should do next.
        Returns a parsed action dict, always with at least {"action": "done"} as fallback.
        """
        elements_json = json.dumps(elements[:60], indent=2)  # Limit to 60 elements to save tokens
        page_snippet = page_text[:3000]

        prompt = SYSTEM_PROMPT_AGENT.format(
            profile_info=profile_info,
            elements_json=elements_json,
            page_text_snippet=page_snippet,
        )

        try:
            raw = await self._call(prompt, json_mode=True)
            return json.loads(raw)
        except Exception as e:
            print(f"[LLM] decide_next_action failed: {e}")
            return {"action": "done", "reason": f"LLM error: {e}"}

    async def find_matching_jobs(self, profile_info: str, keywords: str, page_text: str) -> list:
        """
        Scan a job search results page and return a list of matching job dicts.
        """
        prompt = JOB_SEARCH_PROMPT.format(
            profile_info=profile_info,
            keywords=keywords,
            page_text_snippet=page_text[:4000],
        )
        try:
            raw = await self._call(prompt, json_mode=True)
            data = json.loads(raw)
            # Handle both {"jobs": [...]} and plain [...]
            if isinstance(data, list):
                return data
            return data.get("jobs", data.get("matches", []))
        except Exception as e:
            print(f"[LLM] find_matching_jobs failed: {e}")
            return []

    async def generate_cover_letter(self, profile_info: str, job_description: str) -> str:
        """Generate a tailored cover letter for a specific job."""
        prompt = COVER_LETTER_PROMPT.format(
            profile_info=profile_info,
            job_description=job_description,
        )
        try:
            return await self._call(prompt, json_mode=False)
        except Exception as e:
            print(f"[LLM] generate_cover_letter failed: {e}")
            return ""
