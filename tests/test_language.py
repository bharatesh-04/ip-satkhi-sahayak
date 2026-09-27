import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.llm import MockLLM


def test_mock_llm_honors_selected_language():
    hi = asyncio.run(MockLLM().generate("Need legal guidance", language="hi"))
    kn = asyncio.run(MockLLM().generate("Need legal guidance", language="kn"))

    assert "साक्ष्य" in hi or "कानूनी" in hi or "उत्पाद" in hi
    assert "ಸಮರ್ಥನ" in kn or "ಕಾನೂನು" in kn or "ಪ್ರಾಥಮಿಕ" in kn
