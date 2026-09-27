import json
import uuid
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.schemas import ConsultationRequest, FinalResponse, Claim, Evidence, QueryPlan
from app.services.classifier import profile_from_text, domains_for
from app.services.retrieval import HybridRetriever
from app.services.reranker import rerank
from app.services.trust import EvidenceTrust
from app.services.graph import GraphService
from app.services.llm import get_llm
from app.services.memory import MemoryManager
from app.services.jurisdiction import JurisdictionRouter
from app.services.specialists import run_specialists

DISCLAIMER = "Information only; not legal advice."


class Orchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.graph = GraphService()
        self.llm = get_llm()
        self.memory = MemoryManager(db)
        self.router = JurisdictionRouter()
        self.settings = settings
        self.trust = EvidenceTrust({"PUBLIC"}, demo_mode=settings.demo_mode)
        self.profile_from_text = profile_from_text
        self.domains_for = domains_for
        self.rerank_fn = rerank

    def _audit(self, trace_id: str, user_id: str, event_type: str, payload: dict):
        try:
            from app.db.models import AuditEvent
            self.db.add(AuditEvent(trace_id=trace_id, user_id=user_id, event_type=event_type, payload=payload))
            self.db.commit()
        except Exception:
            self.db.rollback()

    def _jurisdictions(self, req: ConsultationRequest) -> list[str]:
        return self.router.targets(req.jurisdiction_mode.value, req.target_country)

    def _source_pointers(self, req: ConsultationRequest) -> list[dict]:
        if req.jurisdiction_mode.value != "international" or not req.target_country:
            return []
        profile = self.router.load_country_profile(req.target_country)
        return profile.get("authoritative_sources", [])

    def _plan(self, req: ConsultationRequest, domains: list[str], profile) -> QueryPlan:
        jurisdictions = self._jurisdictions(req)
        queries = [req.message]
        if "patents" in domains:
            queries.append("patentability prior art traditional knowledge Ayurvedic formulation")
        if "tk" in domains:
            queries.append("traditional knowledge prior art Ayurveda")
        if "abs" in domains:
            queries.append("biological resources access benefit sharing Ayurveda")
        if "regulation" in domains:
            queries.append("Ayurveda product classification regulatory requirements")
        if "advertising" in domains:
            queries.append("Ayurvedic product advertising health claims requirements")
        if req.jurisdiction_mode.value == "international" and req.target_country:
            queries.append(f"{req.target_country} herbal medicine food cosmetic IP import labelling requirements")
        complexity = "high" if len(domains) >= 4 else "complex" if len(domains) >= 2 else "moderate"
        return QueryPlan(intents=["navigation"], domains=domains, jurisdictions=jurisdictions, complexity=complexity, queries=queries)

    def merge_memory_profile(self, user_id: str, profile):
        stored = self.memory.latest_profile(user_id)
        if not stored or (profile.category != "unknown"):
            return profile
        return stored.model_copy(update={
            "claims": profile.claims or stored.claims,
            "target_markets": profile.target_markets if profile.target_markets != ["IN"] else stored.target_markets,
        })

    def _evidence(self, candidates) -> list[Evidence]:
        out = []
        for c in candidates:
            r = c.row
            out.append(Evidence(
                evidence_id=r.chunk_id, source_id=r.source_id, source_url=r.source_url,
                authority_level=r.authority_level, authority_name=r.authority,
                document_title=r.document_title, jurisdiction=r.jurisdiction, regime=r.regime,
                citation=r.citation, section=r.section, subsection=r.subsection, article=r.article,
                page=r.page, language=r.language, published_at=r.published_at,
                effective_from=r.effective_from, effective_to=r.effective_to, version=r.version,
                status=r.status, access_level=r.access_level, text=r.text,
                relevance_score=c.score, demo_only=bool(getattr(r, "demo_only", False)),
            ))
        return out

    def make_claims(self, evidence: list[Evidence]) -> list[Claim]:
        return [Claim(
            claim_id="C1",
            text="The pathway must be grounded in current, jurisdiction-appropriate evidence.",
            evidence_ids=[e.evidence_id for e in evidence],
        )]

    async def _generate(self, req, profile, plan, evidence, graph_context, memory_records) -> str:
        language = (req.language or "en").lower()
        if settings.llm_provider == "mock":
            product = profile.product_name or profile.category.replace("_", " ")
            market = req.target_country or "India"
            missing = ", ".join(profile.missing_facts) or "none reported"
            source_refs = "; ".join(
                f"[{item.evidence_id}] {item.citation} ({item.jurisdiction}, {item.status})"
                for item in evidence[:3]
            )
            if language == "hi":
                return (
                    f"प्रारंभिक मूल्यांकन: यह {market} के लिए {product} से संबंधित प्रश्न है। "
                    f"प्रोफ़ाइल {profile.classification_confidence:.0%} आत्मविश्वास के साथ है; "
                    f"अभी की आवश्यकता: {missing}। मार्ग चुनने से पहले सटीक फॉर्मूलेशन, उपयोग का उद्देश्य, "
                    "उत्पाद के दावे, निर्माण स्थल और घटक मूल की पुष्टि करें। "
                    f"प्राप्त साक्ष्य: {source_refs}। यह नेविगेशन सहायता है, कानूनी निर्णय नहीं।"
                )[:600]
            if language == "kn":
                return (
                    f"ಪ್ರಾಥಮಿಕ ಮೌಲ್ಯಮಾಪನೆ: ಇದು {market} ಗುರಿಯೊಂದಿಗೆ {product} ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆ. "
                    f"ಪ್ರೊಫೈಲ್ {profile.classification_confidence:.0%} ನಿಶ್ಚಿತತ ಹೊಂದಿದೆ; "
                    f"ಇನ್ನೂ ಅಗತ್ಯವಿರುವ ವಿವರಗಳು: {missing}. ಮಾರ್ಗವನ್ನು ಆಯ್ಕೆ ಮಾಡುವ ಮೊದಲು ನಿಖರವಾದ ಫಾರ್ಮ್ಯುಲೇಷನ್, ಉದ್ದೇಶಿತ ಬಳಕೆ, "
                    "ಉತ್ಪನ್ನದ ಕ್ಲೈಮ್ಗಳು, ತಯಾರಿಕಾ ಸ್ಥಳ ಮತ್ತು ಘಟಕ ಮೂಲಗಳನ್ನು ದೃಢೀಕರಿಸಿ. "
                    f"ಪಡೆಯಲಾದ ಸಮರ್ಥನ: {source_refs}. ಇದು ನ್ಯಾವಿಗೇಷನ್ ನೆರವೇರಿಸುವುದಲ್ಲ, ಕಾನೂನು ನಿರ್ಣಯವಲ್ಲ."
                )[:600]
            return (
                f"Preliminary assessment: this is a {product} query for {market}. "
                f"The profile is {profile.classification_confidence:.0%} confident; "
                f"details still needed: {missing}. Confirm the exact formulation, intended use, "
                "product claims, manufacturing location and ingredient origin before choosing a route. "
                f"Retrieved evidence: {source_refs}. This is navigation support, not a legal determination."
            )[:600]

        evidence_lines = [
            f"{e.evidence_id} | {e.citation} | {e.jurisdiction} | {e.status} | {e.text}" for e in evidence
        ]
        memory_lines = [f"{m.key}: {json.dumps(m.value, ensure_ascii=False)}" for m in memory_records[:5]]
        prompt = (
            "IP-SAKTI evidence-conditioned synthesis.\n"
            f"USER_QUERY: {req.message}\n"
            f"PROFILE: {profile.model_dump()}\n"
            f"PLAN: {plan.model_dump()}\n"
            f"MEMORY_CONTEXT: {memory_lines}\n"
            f"GRAPH_FACTS: {graph_context}\n"
            f"TARGET_LANGUAGE: {language}\n"
            "VERIFIED_EVIDENCE:\n" + "\n".join(evidence_lines) + "\n"
            "Constraints: use only the evidence; preserve jurisdiction and effective dates; "
            "do not fabricate law or citations; state uncertainty; not legal advice; reply in the target language."
        )
        return await self.llm.generate(prompt, language=language)

    def build_response_from_state(self, state: dict) -> FinalResponse:
        req = state["request"]
        profile = state["profile"]
        domains = state.get("domains", [])
        trust = state.get("trust")
        trace_id = state.get("trace_id") or str(uuid.uuid4())
        if state.get("error") == "target_country_required":
            return FinalResponse(
                summary="A target country is required for international guidance.",
                classification=profile.model_dump(), applicable_domains=domains, recommendations=[],
                risks=["Jurisdiction missing"], next_steps=["Select the target country."], human_review=True,
                disclaimer=DISCLAIMER, evidence=[], trace_id=trace_id, memory_used=bool(state.get("memory")), demo_mode=settings.demo_mode,
            )
        if not trust or not trust.eligible:
            warnings = trust.warnings if trust else ["Evidence gate did not run."]
            if not state.get("evidence"):
                jurisdictions = state.get("plan").jurisdictions if state.get("plan") else []
                warnings.append(f"No source records matched requested jurisdiction(s): {', '.join(jurisdictions)}.")
            source_pointers = self._source_pointers(req)
            if source_pointers:
                warnings.append("Official source pointers below are discovery links, not verified evidence.")
            lang = (req.language or "en").lower()
            if lang == "hi":
                summary = (
                    f"मैं वर्तमान में इंडेक्स किए गए साक्ष्य के आधार पर {req.target_country} बाजार-प्रवेश निष्कर्ष का समर्थन नहीं कर सकता। "
                    "नीचे दिए गए आधिकारिक लिंक केवल प्रारंभिक बिंदु हैं; वे आपके उत्पाद के खिलाफ सत्यापित नहीं किए गए हैं। "
                    "पहले सत्यापित करें कि यह खाद्य या दवा के रूप में बेचा जा रहा है, इसका उद्देश्य, सटीक रचना और दावे क्या हैं।"
                    if req.jurisdiction_mode.value == "international"
                    else "मैं उपलब्ध साक्ष्य से विश्वसनीय निष्कर्ष सत्यापित नहीं कर सका। कृपया उत्पाद की जानकारी जोड़ें या अधिकृत स्रोत से परामर्श करें।"
                )
                next_steps = [
                    "उद्देश्यित उपयोग, उत्पाद के दावे, सटीक फॉर्मूलेशन और घटक मूल को सत्यापित करें।",
                    "कानूनी निष्कर्ष पर भरोसा करने से पहले इस अधिकार क्षेत्र के लिए वर्तमान प्राथमिक स्रोतों को इंटीग्रेट करें।",
                ]
            elif lang == "kn":
                summary = (
                    f"ಪ್ರಸ್ತುತ ಇಂಡೆಕ್ಸ್ಡ್ ಸಮರ್ಥನಗಳ ಆಧಾರದ ಮೇಲೆ {req.target_country} ಮಾರುಕಟ್ಟೆ-ಪ್ರವೇಶ ತೀರ್ಮಾನವನ್ನು ನಾನು ಬೆಂಬಲಿಸಲಾರೆನು. "
                    "ಕೆಳಗಿನ ಅಧಿಕೃತ ಲಿಂಕ್ಗಳು ಕೇವಲ ಪ್ರಾರಂಭಿಕ ಬಿಂದುಗಳಾಗಿವೆ; ಅವು ನಿಮ್ಮ ಉತ್ಪನ್ನಕ್ಕೆ ಸಂಬಂಧಿಸಿದಂತೆ ಪರಿಶೀಲಿಸಿಲ್ಲ. "
                    "ಮೊದಲಿಗೆ ಇದು ಆಹಾರ ಅಥವಾ ಔಷಧಿಯಾಗಿ ಮಾರಾಟವಾಗುತ್ತಿದೆಯೇ, ಅದರ ಉದ್ದೇಶ, ನಿಖರ ಸಂಯೋಜನೆ ಮತ್ತು ಕ್ಲೈಮ್ಗಳು ಯಾವುವು ಎಂಬುದನ್ನು ದೃಢೀಕರಿಸಿ."
                    if req.jurisdiction_mode.value == "international"
                    else "ಲಭ್ಯವಿರುವ ಸಮರ್ಥನಗಳಿಂದ ವಿಶ್ವಾಸಾರ್ಹ ತೀರ್ಮಾನವನ್ನು ನಾನು ಪರಿಶೀಲಿಸದಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಉತ್ಪನ್ನ ವಿವರಗಳನ್ನು ಸೇರಿಸಿ ಅಥವಾ ಅಧಿಕೃತ ಮೂಲದೊಂದಿಗೆ ಸಮಾಲೋಚಿಸಿ."
                )
                next_steps = [
                    "ಉದ್ದೇಶಿತ ಬಳಕೆ, ಉತ್ಪನ್ನದ ಕ್ಲೈಮ್ಗಳು, ನಿಖರ ಫಾರ್ಮ್ಯುಲೇಷನ್ ಮತ್ತು ಘಟಕ ಮೂಲವನ್ನು ಪರಿಶೀಲಿಸಿ.",
                    "ಕಾನೂನು ತೀರ್ಮಾನಗಳಲ್ಲಿ ನಂಬಿಕೆ ಇಡಲು ಈ ಅಧಿಕಾರ ಪ್ರದೇಶದ ಪ್ರಸ್ತುತ ಪ್ರಾಥಮಿಕ ಮೂಲಗಳನ್ನು ಇಂಟಿಗ್ರೇಟ್ ಮಾಡಿ.",
                ]
            else:
                summary = (
                    f"I can't support a {req.target_country} market-entry conclusion from the evidence currently indexed. "
                    "The official links below are starting points only; they have not been checked against your product. "
                    "First confirm whether this is sold as food or medicine, its intended use, exact composition and claims."
                    if req.jurisdiction_mode.value == "international"
                    else "I could not verify a reliable conclusion from the available evidence. Please add product details or consult an authorized source."
                )
                next_steps = [
                    "Confirm intended use, product claims, exact formulation and ingredient origin.",
                    "Ingest current primary sources for this jurisdiction before relying on a legal conclusion.",
                ]
            return FinalResponse(
                summary=summary,
                classification=profile.model_dump(), applicable_domains=domains, recommendations=[], risks=warnings,
                next_steps=next_steps,
                human_review=True, disclaimer=DISCLAIMER, evidence=[], trace_id=trace_id,
                memory_used=bool(state.get("memory")), demo_mode=settings.demo_mode,
                source_pointers=source_pointers,
                international_profile={"country": req.target_country, "mode": "GLOBAL_FRAMEWORK + COUNTRY_PROFILE"} if req.jurisdiction_mode.value == "international" else None,
            )
        evidence_ids = []
        for e in trust.eligible:
            if e.evidence_id not in evidence_ids:
                evidence_ids.append(e.evidence_id)
            if len(evidence_ids) >= 2:
                break
        recs=[]
        if "patents" in domains:
            recs.append({"text":"Run patentability and prior-art screening before treating the innovation as protectable.","why":"Patent/IP objective detected.","citations":evidence_ids,"confidence":"high" if trust.confidence>=.82 else "moderate"})
        if "tk" in domains:
            recs.append({"text":"Check traditional-knowledge overlap using authorized TK/prior-art evidence.","why":"Traditional-knowledge indicator detected.","citations":evidence_ids,"confidence":"moderate"})
        if "abs" in domains:
            recs.append({"text":"Assess biological-resource origin and ABS applicability before commercialisation.","why":"Biological-resource indicator detected.","citations":evidence_ids,"confidence":"moderate"})
        if "regulation" in domains:
            recs.append({"text":"Confirm the product category before relying on a regulatory route.","why":"Classification changes the applicable regulatory framework.","citations":evidence_ids,"confidence":"high"})
        if req.jurisdiction_mode.value == "international":
            recs.append({"text":f"Apply {req.target_country.upper()} rules through the country profile plus applicable global frameworks.","why":"The destination market has separate requirements.","citations":evidence_ids,"confidence":"moderate"})
        risks=list(trust.warnings)
        if profile.classification_confidence < .65: risks.append("Product classification remains uncertain.")
        if trust.confidence < .8: risks.append("Evidence confidence is below the high-confidence threshold.")
        if settings.demo_mode: risks.append("Demo mode: seeded evidence is illustrative and is not controlling law.")
        return FinalResponse(
            summary=(state.get("generation") or "IP-SAKTI produced an evidence-gated preliminary pathway.")[:600],
            classification={"category":profile.category,"confidence":profile.classification_confidence,"missing_facts":profile.missing_facts},
            applicable_domains=domains,recommendations=recs,risks=risks,
            next_steps=["Confirm product classification and intended claims.","Review exact citations and source versions.","Complete TK/ABS and target-market checks where applicable.","Use human expert review for high-risk/conflicting cases."],
            human_review=trust.needs_human,disclaimer=DISCLAIMER,evidence=trust.eligible,trace_id=trace_id,
            memory_used=bool(state.get("memory")),demo_mode=settings.demo_mode,
            source_pointers=self._source_pointers(req),
            international_profile={"country":req.target_country,"mode":"GLOBAL_FRAMEWORK + COUNTRY_PROFILE"} if req.jurisdiction_mode.value=="international" else None,
        )

    async def _run_deterministic(self, req: ConsultationRequest, trace_id: str) -> FinalResponse:
        self._audit(trace_id, req.user_id, "query_received", {"language": req.language, "mode": req.jurisdiction_mode.value, "target_country": req.target_country})
        memory_records = self.memory.relevant(req.user_id, limit=8)
        profile = self.merge_memory_profile(req.user_id, profile_from_text(req.message))
        domains = domains_for(req.message, profile)

        if req.jurisdiction_mode.value == "international" and not req.target_country:
            self._audit(trace_id, req.user_id, "jurisdiction_missing", {})
            return FinalResponse(
                summary="A target country is required for international guidance.",
                classification=profile.model_dump(), applicable_domains=domains, recommendations=[],
                risks=["Jurisdiction missing"], next_steps=["Select the target country."], human_review=True,
                disclaimer=DISCLAIMER, evidence=[], trace_id=trace_id, memory_used=bool(memory_records), demo_mode=settings.demo_mode,
            )

        profile.target_markets = [req.target_country.upper()] if req.jurisdiction_mode.value == "international" and req.target_country else profile.target_markets
        self.memory.save_profile(req.user_id, profile)
        plan = self._plan(req, domains, profile)
        self._audit(trace_id, req.user_id, "query_planned", plan.model_dump())

        candidates = []
        for q in plan.queries:
            candidates.extend(self.retriever.search(q, plan.jurisdictions, top_k=10))
        candidates = rerank(req.message, candidates, top_k=settings.rerank_top_k)
        evidence = self._evidence(candidates[:settings.max_evidence_items])
        self._audit(trace_id, req.user_id, "evidence_retrieved", {"count": len(evidence), "ids": [e.evidence_id for e in evidence]})

        entities = [x.name for x in profile.ingredients] + profile.target_markets
        graph_context = self.graph.expand(entities, plan.jurisdictions) if settings.enable_graph_rag and plan.complexity != "moderate" else []
        trust = self.trust.verify(evidence, plan.jurisdictions, self.make_claims(evidence))
        self._audit(trace_id, req.user_id, "evidence_verified", {"confidence": trust.confidence, "warnings": trust.warnings, "eligible": len(trust.eligible)})
        specialist_results = run_specialists(profile, domains, [e.evidence_id for e in trust.eligible], req.target_country or "IN")
        self._audit(trace_id, req.user_id, "specialists_selected", {"roles": [v["role"] for v in specialist_results.values()], "complexity": plan.complexity})

        if not trust.eligible:
            risks = list(trust.warnings)
            if not evidence:
                risks.append(f"No source records matched requested jurisdiction(s): {', '.join(plan.jurisdictions)}.")
            source_pointers = self._source_pointers(req)
            if source_pointers:
                risks.append("Official source pointers below are discovery links, not verified evidence.")
            lang = (req.language or "en").lower()
            if lang == "hi":
                summary = (
                    f"मैं वर्तमान में इंडेक्स किए गए साक्ष्य के आधार पर {req.target_country} बाजार-प्रवेश निष्कर्ष का समर्थन नहीं कर सकता। "
                    "नीचे दिए गए आधिकारिक लिंक केवल प्रारंभिक बिंदु हैं; वे आपके उत्पाद के खिलाफ सत्यापित नहीं किए गए हैं। "
                    "पहले सत्यापित करें कि यह खाद्य या दवा के रूप में बेचा जा रहा है, इसका उद्देश्य, सटीक रचना और दावे क्या हैं।"
                    if req.jurisdiction_mode.value == "international"
                    else "मैं उपलब्ध साक्ष्य से विश्वसनीय निष्कर्ष सत्यापित नहीं कर सका। कृपया उत्पाद की जानकारी जोड़ें या अधिकृत स्रोत से परामर्श करें।"
                )
                next_steps = [
                    "उद्देश्यित उपयोग, उत्पाद के दावे, सटीक फॉर्मूलेशन और घटक मूल को सत्यापित करें।",
                    "कानूनी निष्कर्ष पर भरोसा करने से पहले इस अधिकार क्षेत्र के लिए वर्तमान प्राथमिक स्रोतों को इंटीग्रेट करें।",
                ]
            elif lang == "kn":
                summary = (
                    f"ಪ್ರಸ್ತುತ ಇಂಡೆಕ್ಸ್ಡ್ ಸಮರ್ಥನಗಳ ಆಧಾರದ ಮೇಲೆ {req.target_country} ಮಾರುಕಟ್ಟೆ-ಪ್ರವೇಶ ತೀರ್ಮಾನವನ್ನು ನಾನು ಬೆಂಬಲಿಸಲಾರೆನು. "
                    "ಕೆಳಗಿನ ಅಧಿಕೃತ ಲಿಂಕ್ಗಳು ಕೇವಲ ಪ್ರಾರಂಭಿಕ ಬಿಂದುಗಳಾಗಿವೆ; ಅವು ನಿಮ್ಮ ಉತ್ಪನ್ನಕ್ಕೆ ಸಂಬಂಧಿಸಿದಂತೆ ಪರಿಶೀಲಿಸಿಲ್ಲ. "
                    "ಮೊದಲಿಗೆ ಇದು ಆಹಾರ ಅಥವಾ ಔಷಧಿಯಾಗಿ ಮಾರಾಟವಾಗುತ್ತಿದೆಯೇ, ಅದರ ಉದ್ದೇಶ, ನಿಖರ ಸಂಯೋಜನೆ ಮತ್ತು ಕ್ಲೈಮ್ಗಳು ಯಾವುವು ಎಂಬುದನ್ನು ದೃಢೀಕರಿಸಿ."
                    if req.jurisdiction_mode.value == "international"
                    else "ಲಭ್ಯವಿರುವ ಸಮರ್ಥನಗಳಿಂದ ವಿಶ್ವಾಸಾರ್ಹ ತೀರ್ಮಾನವನ್ನು ನಾನು ಪರಿಶೀಲಿಸದಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಉತ್ಪನ್ನ ವಿವರಗಳನ್ನು ಸೇರಿಸಿ ಅಥವಾ ಅಧಿಕೃತ ಮೂಲದೊಂದಿಗೆ ಸಮಾಲೋಚಿಸಿ."
                )
                next_steps = [
                    "ಉದ್ದೇಶಿತ ಬಳಕೆ, ಉತ್ಪನ್ನದ ಕ್ಲೈಮ್ಗಳು, ನಿಖರ ಫಾರ್ಮ್ಯುಲೇಷನ್ ಮತ್ತು ಘಟಕ ಮೂಲವನ್ನು ಪರಿಶೀಲಿಸಿ.",
                    "ಕಾನೂನು ತೀರ್ಮಾನಗಳಲ್ಲಿ ನಂಬಿಕೆ ಇಡಲು ಈ ಅಧಿಕಾರ ಪ್ರದೇಶದ ಪ್ರಸ್ತುತ ಪ್ರಾಥಮಿಕ ಮೂಲಗಳನ್ನು ಇಂಟಿಗ್ರೇಟ್ ಮಾಡಿ.",
                ]
            else:
                summary = (
                    f"I can't support a {req.target_country} market-entry conclusion from the evidence currently indexed. "
                    "The official links below are starting points only; they have not been checked against your product. "
                    "First confirm whether this is sold as food or medicine, its intended use, exact composition and claims."
                    if req.jurisdiction_mode.value == "international"
                    else "I could not verify a reliable conclusion from the available evidence. Please add product details or consult an authorized source."
                )
                next_steps = [
                    "Confirm intended use, product claims, exact formulation and ingredient origin.",
                    "Ingest current primary sources for this jurisdiction before relying on a legal conclusion.",
                ]
            return FinalResponse(
                summary=summary,
                classification=profile.model_dump(), applicable_domains=domains, recommendations=[], risks=risks,
                next_steps=next_steps,
                human_review=True, disclaimer=DISCLAIMER, evidence=[], trace_id=trace_id,
                memory_used=bool(memory_records), demo_mode=settings.demo_mode,
                source_pointers=source_pointers,
                international_profile={"country": req.target_country, "mode": "GLOBAL_FRAMEWORK + COUNTRY_PROFILE"} if req.jurisdiction_mode.value == "international" else None,
            )

        generation = await self._generate(req, profile, plan, trust.eligible, graph_context, memory_records)
        evidence_ids = [e.evidence_id for e in trust.eligible[:2]]
        recs = []
        if "patents" in domains:
            recs.append({"text": "Run patentability and prior-art screening before treating the innovation as protectable.", "why": "Patent/IP objective detected.", "citations": evidence_ids, "confidence": "high" if trust.confidence >= .82 else "moderate"})
        if "tk" in domains:
            recs.append({"text": "Check traditional-knowledge overlap using authorized TK/prior-art evidence.", "why": "Traditional-knowledge indicator detected.", "citations": evidence_ids, "confidence": "moderate"})
        if "abs" in domains:
            recs.append({"text": "Assess biological-resource origin and ABS applicability before commercialisation.", "why": "Biological-resource indicator detected.", "citations": evidence_ids, "confidence": "moderate"})
        if "regulation" in domains:
            recs.append({"text": "Confirm the product category before relying on a regulatory route.", "why": "Classification changes the applicable regulatory framework.", "citations": evidence_ids, "confidence": "high"})
        if req.jurisdiction_mode.value == "international":
            recs.append({"text": f"Apply {req.target_country.upper()} rules through the country profile plus applicable global frameworks.", "why": "The destination market has separate requirements.", "citations": evidence_ids, "confidence": "moderate"})

        risks = list(trust.warnings)
        if profile.classification_confidence < .65:
            risks.append("Product classification remains uncertain.")
        if trust.confidence < .8:
            risks.append("Evidence confidence is below the high-confidence threshold.")
        if settings.demo_mode:
            risks.append("Demo mode: seeded evidence is illustrative and is not controlling law.")

        self._audit(trace_id, req.user_id, "response_generated", {"confidence": trust.confidence, "human_review": trust.needs_human})
        return FinalResponse(
            summary= generation[:600] if generation else "IP-SAKTI produced an evidence-gated preliminary pathway.",
            classification={"category": profile.category, "confidence": profile.classification_confidence, "missing_facts": profile.missing_facts},
            applicable_domains=domains, recommendations=recs, risks=risks,
            next_steps=["Confirm product classification and intended claims.", "Review exact citations and source versions.", "Complete TK/ABS and target-market checks where applicable.", "Use human expert review for high-risk/conflicting cases."],
            human_review=trust.needs_human, disclaimer=DISCLAIMER, evidence=trust.eligible,
            trace_id=trace_id, memory_used=bool(memory_records), demo_mode=settings.demo_mode,
            source_pointers=self._source_pointers(req),
            international_profile={"country": req.target_country, "mode": "GLOBAL_FRAMEWORK + COUNTRY_PROFILE"} if req.jurisdiction_mode.value == "international" else None,
        )

    async def run(self, req: ConsultationRequest) -> FinalResponse:
        trace_id = str(uuid.uuid4())
        if settings.enable_multi_agent:
            try:
                from app.services.workflow import LANGGRAPH_AVAILABLE, build_graph
                if LANGGRAPH_AVAILABLE:
                    state = await build_graph(self).ainvoke({"request": req, "trace_id": trace_id})
                    result = state.get("result")
                    if result is not None:
                        self._audit(trace_id, req.user_id, "langgraph_completed", {"domains": state.get("domains", []), "confidence": getattr(state.get("trust"), "confidence", None)})
                        return result
            except Exception as exc:
                self._audit(trace_id, req.user_id, "langgraph_fallback", {"error": type(exc).__name__})
        return await self._run_deterministic(req, trace_id)
