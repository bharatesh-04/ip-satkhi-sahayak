from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_env: str = "development"
    app_version: str = "0.1.0"
    demo_mode: bool = True

    # Hackathon default: local SQLite keeps the repo runnable without Docker.
    # Docker/production uses PostgreSQL + pgvector via DATABASE_URL.
    database_url: str = "sqlite:///./ip_sakti_dev.db"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ip-sakti-demo"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "ip-sakti-evidence"

    jwt_secret: str = "change-me"
    jwt_issuer: str = "ip-sakti"
    jwt_audience: str = "ip-sakti-client"

    # Model-agnostic provider routing. Use mock for deterministic demo mode.
    llm_provider: str = "mock"  # mock | ollama | openai
    llm_model: str = "gemma3:4b"
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    api_key: str = ""
    require_api_key: bool = False
    api_key_header: str = "X-API-Key"
    enable_rate_limit: bool = False
    rate_limit_per_minute: int = 60

    embedding_provider: str = "hash"  # hash | embeddinggemma adapter later
    embedding_model: str = "multilingual-demo"
    reranker_provider: str = "heuristic"

    bhashini_enabled: bool = False
    bhashini_api_url: str = ""
    bhashini_api_key: str = ""

    lexical_retriever: str = "postgres"
    enable_graph_rag: bool = True
    enable_multi_agent: bool = True
    enable_adaptive_retrieval: bool = True
    enable_voice: bool = False
    enable_paid_connectors: bool = False
    enable_restricted_tkdl: bool = False
    enable_expert_handoff: bool = True

    max_retrieval_retries: int = 2
    default_top_k: int = 20
    rerank_top_k: int = 8
    max_evidence_items: int = 8
    max_agent_iterations: int = 3

    audit_logging: bool = True
    restricted_source_policy: bool = True

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
