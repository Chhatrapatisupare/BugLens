"""
BugLens Groq Service.
Manages LLM reasoning calls using the official Groq SDK with JSON-enforced output,
model configurability, retry mechanisms, and safe fallback handling.
"""
import os
import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY is not configured in the environment.")
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    def generate_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """
        Calls Groq chat completion demanding a valid JSON response.
        If initial parsing fails, retries once with an explicit schema reminder.
        """
        if not self.is_configured():
            raise ValueError("Groq API key is missing or not configured. Set GROQ_API_KEY in .env.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        attempt = 0
        while attempt <= retry_count:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )

                raw_content = response.choices[0].message.content or "{}"
                parsed_json = self._extract_json(raw_content)
                if parsed_json is not None:
                    return parsed_json

                logger.warning("Groq response could not be parsed as JSON on attempt %d. Raw text: %s", attempt, raw_content[:200])

            except Exception as e:
                logger.error("Groq API error on attempt %d: %s", attempt, str(e))
                if attempt == retry_count:
                    raise RuntimeError(f"Groq API error: {str(e)}")

            # Prepare retry prompt
            messages.append({
                "role": "user",
                "content": "IMPORTANT: Your previous response was not valid JSON. Provide ONLY valid RFC-8259 JSON format with NO markdown wrapping and NO commentary."
            })
            attempt += 1

        raise ValueError("Failed to obtain valid JSON from Groq after retries.")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely extracts JSON from raw string or markdown code fences."""
        text = text.strip()
        # Direct parse attempt
        try:
            return json.loads(text)
        except Exception:
            pass

        # Match markdown ```json ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Match first '{' to last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass

        return None
