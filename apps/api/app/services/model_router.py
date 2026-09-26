"""Provider-agnostic routing for LLM, embedding and reranking capabilities."""
from dataclasses import dataclass
from app.core.config import settings


@dataclass(frozen=True)
class ModelRoute:
    task: str
    provider: str
    model: str
    reason: str


class ModelRouter:
    def route(self, task: str, complexity: str = "moderate") -> ModelRoute:
        if task in {"classify", "extract", "rewrite"} and complexity != "high":
            return ModelRoute(task, settings.llm_provider, settings.llm_model, "fast-path task")
        if task in {"reason", "synthesize"}:
            return ModelRoute(task, settings.llm_provider, settings.llm_model, "evidence-conditioned reasoning")
        return ModelRoute(task, settings.llm_provider, settings.llm_model, "default configured route")
