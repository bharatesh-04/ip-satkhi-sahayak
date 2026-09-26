from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JurisdictionMode(str, Enum):
    india = "india"
    international = "international"


class MemoryType(str, Enum):
    innovation = "innovation"
    preference = "preference"
    episodic = "episodic"
    semantic = "semantic"
    task = "task"


class InnovationIngredient(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    part_used: Optional[str] = None
    source: Optional[str] = None


class InnovationProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    profile_id: Optional[str] = None
    product_name: Optional[str] = None
    category: str = "unknown"
    ingredients: list[InnovationIngredient] = Field(default_factory=list)
    intended_use: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    traditional_knowledge_involvement: str = "unknown"
    biological_resource_involvement: str = "unknown"
    origin: Optional[str] = None
    innovation_delta: list[str] = Field(default_factory=list)
    target_markets: list[str] = Field(default_factory=lambda: ["IN"])
    classification_confidence: float = 0.0
    missing_facts: list[str] = Field(default_factory=list)


class ConsultationRequest(BaseModel):
    message: str
    language: str = "en"
    jurisdiction_mode: JurisdictionMode = JurisdictionMode.india
    target_country: Optional[str] = None
    consultation_id: Optional[str] = None
    user_id: str = "demo-user"

    _SUPPORTED_COUNTRY_CODES = {"IN", "DE", "US", "AE", "JP", "AU", "BR"}

    @field_validator("target_country", mode="before")
    @classmethod
    def normalize_target_country(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("target_country must be a string")
        normalized = value.strip()
        if not normalized:
            return None
        return normalized.upper()

    @model_validator(mode="after")
    def validate_country_selection(self):
        if self.jurisdiction_mode == JurisdictionMode.international:
            if not self.target_country:
                raise ValueError("target_country is required for international consultations")
            if len(self.target_country) != 2 or not self.target_country.isalpha():
                raise ValueError("target_country must be a valid 2-letter ISO country code")
            if self.target_country.upper() not in self._SUPPORTED_COUNTRY_CODES:
                raise ValueError(
                    "target_country must be one of: IN, DE, US, AE, JP, AU, BR"
                )
        return self


class Evidence(BaseModel):
    evidence_id: str
    source_id: str
    source_url: str
    authority_level: str
    authority_name: str
    document_title: str
    jurisdiction: str
    regime: str
    citation: str
    section: Optional[str] = None
    subsection: Optional[str] = None
    article: Optional[str] = None
    page: Optional[int] = None
    language: str = "en"
    published_at: Optional[datetime] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    version: Optional[str] = None
    status: str = "current"
    access_level: str = "PUBLIC"
    text: str
    relevance_score: float = 0.0
    verified: bool = False
    demo_only: bool = False


class Claim(BaseModel):
    claim_id: str
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    status: str = "UNVERIFIED"


class QueryPlan(BaseModel):
    intents: list[str]
    domains: list[str]
    jurisdictions: list[str]
    complexity: str = "moderate"
    queries: list[str] = Field(default_factory=list)


class FinalResponse(BaseModel):
    summary: str
    classification: dict[str, Any]
    applicable_domains: list[str]
    recommendations: list[dict[str, Any]]
    risks: list[str]
    next_steps: list[str]
    human_review: bool
    disclaimer: str = "Information only; not legal advice."
    evidence: list[Evidence] = Field(default_factory=list)
    source_pointers: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str
    memory_used: bool = False
    demo_mode: bool = False
    international_profile: Optional[dict[str, Any]] = None


class MemoryRecord(BaseModel):
    memory_id: Optional[str] = None
    user_id: str
    memory_type: MemoryType
    key: str
    value: dict[str, Any]
    source: str = "user"
    confidence: float = 1.0
    expires_at: Optional[datetime] = None
