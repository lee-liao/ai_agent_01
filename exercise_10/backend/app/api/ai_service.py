from datetime import datetime
from typing import Dict, List, Optional

from openai import AsyncOpenAI


class AIAssistantService:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self.client: Optional[AsyncOpenAI] = None
        self.conversation_history: Dict[str, List[Dict]] = {}

    async def generate_suggestion(self, call_id: str, customer_message: str) -> Dict:
        """Generate agent suggestion based on customer transcript."""
        # Basic fallback if not configured
        if not self._api_key:
            return {
                "suggestion": "Acknowledge the issue, show empathy, and ask a clarifying question.",
                "confidence": 0.5,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Track brief history (last 5 messages)
        self.conversation_history.setdefault(call_id, [])
        self.conversation_history[call_id].append({"role": "user", "content": customer_message})
        history = self.conversation_history[call_id][-5:]

        system_prompt = (
            "You help call center agents. Given the customer's message, "
            "suggest a concrete next step, with brief reasoning. Return concise text."
        )

        try:
            if self.client is None:
                self.client = AsyncOpenAI(api_key=self._api_key)
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}, *history],
                temperature=0.7,
                max_tokens=120,
            )
            content = resp.choices[0].message.content if resp.choices else ""
            return {
                "suggestion": content or "Ask a clarifying question and summarize the issue.",
                "confidence": 0.8,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception:
            return {
                "suggestion": "Acknowledge the issue, show empathy, and ask a clarifying question.",
                "confidence": 0.6,
                "timestamp": datetime.utcnow().isoformat(),
            }
