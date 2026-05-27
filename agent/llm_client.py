import json
from openai import AsyncOpenAI
from agent.prompts import SYSTEM_PROMPT_AGENT, COVER_LETTER_PROMPT

class LLMClient:
    def __init__(self, api_key: str):
        # Using GitHub Models API compatibility
        self.client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
        # Using gpt-4o-mini as default for GitHub Models to save rate limits
        self.model = "gpt-4o-mini"

    async def decide_next_action(self, profile_info, elements, page_text):
        elements_json = json.dumps(elements, indent=2)
        page_snippet = page_text[:2000] # Pass first 2000 chars for context
        
        prompt = SYSTEM_PROMPT_AGENT.format(
            profile_info=profile_info,
            elements_json=elements_json,
            page_text_snippet=page_snippet
        )

        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {"action": "done"}

    async def generate_cover_letter(self, profile_info, job_description):
        prompt = COVER_LETTER_PROMPT.format(
            profile_info=profile_info,
            job_description=job_description
        )
        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model
        )
        return response.choices[0].message.content.strip()
