from typing import Any
import httpx
from app.core.config import settings


class LLMProvider:
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLM(LLMProvider):
    async def generate(self, prompt: str) -> str:
        return "Evidence package received. Final legal conclusions must be generated only from the verified evidence supplied to the model."


class OllamaLLM(LLMProvider):
    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.llm_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "")


class OpenAICompatibleLLM(LLMProvider):
    async def generate(self, prompt: str) -> str:
        if not settings.openai_api_key:
            return await MockLLM().generate(prompt)
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": "You are IP-SAKTI Sahayak. Use only VERIFIED_EVIDENCE for material legal claims. Do not invent law or citations."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{settings.openai_base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def get_llm() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaLLM()
    if settings.llm_provider in {"openai", "hosted"}:
        return OpenAICompatibleLLM()
    return MockLLM()
