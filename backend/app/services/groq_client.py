from __future__ import annotations

import json
from typing import Any, Dict, List

import requests
from fastapi import HTTPException

from app.core.config import settings


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is missing in .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=35)
            if response.status_code == 400 and "response_format" in response.text:
                payload.pop("response_format", None)
                response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=35)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=f"Groq API request failed: {exc}") from exc

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        candidate = text.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise HTTPException(status_code=502, detail="Could not parse structured output from Groq")

        try:
            return json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Could not parse structured output from Groq") from exc

    def plan_sql(self, messages: List[Dict[str, str]], temperature: float = 0.05) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        data = self._request(payload)

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(status_code=502, detail="Unexpected response from Groq API") from exc

        parsed = self._extract_json(content)
        parsed.setdefault("action", "deny")
        parsed.setdefault("sql", "")
        parsed.setdefault("params", {})
        parsed.setdefault("assistant_message", "I processed your request.")
        return parsed


groq_client = GroqClient(api_key=settings.groq_api_key, model=settings.groq_model)
