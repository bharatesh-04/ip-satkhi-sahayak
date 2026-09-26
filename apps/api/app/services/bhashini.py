from app.core.config import settings


class BhashiniAdapter:
    """Provider-neutral adapter. Live API wiring is enabled only with credentials."""
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not settings.bhashini_enabled or not settings.bhashini_api_url or not settings.bhashini_api_key:
            return text
        # Keep provider-specific implementation isolated here.
        return text

    async def speech_to_text(self, audio_bytes: bytes, language: str) -> str:
        raise NotImplementedError("Configure Bhashini ASR credentials for live voice mode.")

    async def text_to_speech(self, text: str, language: str) -> bytes:
        raise NotImplementedError("Configure Bhashini TTS credentials for live voice mode.")
