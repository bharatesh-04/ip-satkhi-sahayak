from typing import Any
import httpx
from app.core.config import settings


class LLMProvider:
    async def generate(self, prompt: str, language: str = "en") -> str:
        raise NotImplementedError


class MockLLM(LLMProvider):
    async def generate(self, prompt: str, language: str = "en") -> str:
        lang = (language or "en").lower()
        if lang == "hi":
            return "साक्ष्य पैकेज प्राप्त हुआ है। अंतिम कानूनी निष्कर्ष केवल सत्यापित साक्ष्य पर आधारित होना चाहिए।"
        if lang == "kn":
            return "ಸಮರ್ಥನ ಪ್ಯಾಕೇಜ್ ಸ್ವಿಕರಿಸಲಾಗಿದೆ. ಅಂತಿಮ ಕಾನೂನು ತೀರ್ಮಾನಗಳು ಕೇವಲ ಪರಿಶೀಲಿಸಿದ ಸಮರ್ಥನಗಳ ಆಧಾರದ ಮೇಲೆ ಇರಬೇಕು."
        return "Evidence package received. Final legal conclusions must be generated only from the verified evidence supplied to the model."


class OllamaLLM(LLMProvider):
    async def generate(self, prompt: str, language: str = "en") -> str:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.llm_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "")


class OpenAICompatibleLLM(LLMProvider):
    async def generate(self, prompt: str, language: str = "en") -> str:
        if not settings.openai_api_key:
            return await MockLLM().generate(prompt, language=language)
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": "You are IP-SAKTI Sahayak. Use only VERIFIED_EVIDENCE for material legal claims. Do not invent law or citations. Always answer in the user's selected language."},
                {"role": "user", "content": f"Respond in {language} language.\n\n{prompt}"},
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
