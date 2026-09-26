"""Optional LangGraph workflow for the controlled IP-SAKTI reasoning path."""
from typing import TypedDict, Any

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except Exception:
    StateGraph = None
    END = None
    LANGGRAPH_AVAILABLE = False


class LegalGraphState(TypedDict, total=False):
    request: Any
    profile: Any
    domains: list[str]
    plan: Any
    candidates: list[Any]
    evidence: list[Any]
    graph_context: list[dict]
    trust: Any
    memory: list[Any]
    specialist_results: dict[str, dict]
    generation: str
    error: str


def build_graph(service):
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph is not installed")

    async def parse_input(state: LegalGraphState):
        req = state["request"]
        state["profile"] = service.profile_from_text(req.message)
        state["domains"] = service.domains_for(req.message, state["profile"])
        return state

    async def check_profile(state: LegalGraphState):
        req = state["request"]
        state["memory"] = service.memory.relevant(req.user_id, limit=8)
        state["profile"] = service.merge_memory_profile(req.user_id, state["profile"])
        return state

    async def classify_and_route(state: LegalGraphState):
        req = state["request"]
        if req.jurisdiction_mode.value == "international" and not req.target_country:
            state["error"] = "target_country_required"
            return state
        state["plan"] = service._plan(req, state["domains"], state["profile"])
        state["profile"].target_markets = [req.target_country.upper()] if req.jurisdiction_mode.value == "international" else state["profile"].target_markets
        service.memory.save_profile(req.user_id, state["profile"])
        return state

    async def retrieve(state: LegalGraphState):
        if state.get("error"):
            return state
        candidates = []
        for q in state["plan"].queries:
            candidates.extend(service.retriever.search(q, state["plan"].jurisdictions, top_k=10))
        state["candidates"] = service.rerank_fn(state["request"].message, candidates, top_k=8)
        state["evidence"] = service._evidence(state["candidates"][:service.settings.max_evidence_items])
        return state

    async def graph_expand(state: LegalGraphState):
        if state.get("error"):
            return state
        profile = state["profile"]
        entities = [x.name for x in profile.ingredients] + profile.target_markets
        state["graph_context"] = service.graph.expand(entities, state["plan"].jurisdictions) if service.settings.enable_graph_rag else []
        return state

    async def evidence_gate(state: LegalGraphState):
        if state.get("error"):
            return state
        state["trust"] = service.trust.verify(state["evidence"], state["plan"].jurisdictions, service.make_claims(state["evidence"]))
        return state

    async def specialists(state: LegalGraphState):
        if state.get("error") or not state.get("trust") or not state["trust"].eligible:
            return state
        from app.services.specialists import run_specialists
        state["specialist_results"] = run_specialists(state["profile"], state["domains"], [e.evidence_id for e in state["trust"].eligible], state["request"].target_country or "IN")
        return state

    async def synthesize(state: LegalGraphState):
        if state.get("error") or not state.get("trust") or not state["trust"].eligible:
            return state
        state["generation"] = await service._generate(
            state["request"], state["profile"], state["plan"], state["trust"].eligible,
            state.get("graph_context", []), state.get("memory", [])
        )
        return state

    async def finalize(state: LegalGraphState):
        state["result"] = service.build_response_from_state(state)
        return state

    graph = StateGraph(LegalGraphState)
    graph.add_node("parse_input", parse_input)
    graph.add_node("check_profile", check_profile)
    graph.add_node("classify_and_route", classify_and_route)
    graph.add_node("retrieve", retrieve)
    graph.add_node("graph_expand", graph_expand)
    graph.add_node("evidence_gate", evidence_gate)
    graph.add_node("specialists", specialists)
    graph.add_node("synthesize", synthesize)
    graph.add_node("finalize", finalize)
    graph.set_entry_point("parse_input")
    graph.add_edge("parse_input", "check_profile")
    graph.add_edge("check_profile", "classify_and_route")
    graph.add_edge("classify_and_route", "retrieve")
    graph.add_edge("retrieve", "graph_expand")
    graph.add_edge("graph_expand", "evidence_gate")
    graph.add_edge("evidence_gate", "specialists")
    graph.add_edge("specialists", "synthesize")
    graph.add_edge("synthesize", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()
