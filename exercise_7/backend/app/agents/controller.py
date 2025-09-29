import asyncio
from typing import Dict, Any, Tuple

from app.config import settings
from .router import route
from .tools import SearchTool, PriceTool, CacheTool, ToolResult
from .retry import execute_with_policies
from .circuit_breaker import circuit_breaker
from .idempotency import make_idempotency_key
from .rerank import rerank_top_one
from .tracing import span


TOOLS = {
    "SearchTool": SearchTool(),
    "PriceTool": PriceTool(),
    "CacheTool": CacheTool(),
}


async def react_recover(query: str, context: Dict[str, Any]) -> ToolResult:
    # Simple ReAct stub: try cache as a degraded fallback for price
    tool = TOOLS["CacheTool"]
    return await tool.invoke(query, context)


async def run_plan(trace_id: str, query: str) -> Dict[str, Any]:
    context: Dict[str, Any] = {}

    # Plan nodes: search -> price
    async def run_node(node: str, parent_span_id: str | None) -> Tuple[bool, str | None]:
        tool_name = route(query, node)
        # Circuit breaker selection
        if node == "price" and circuit_breaker.is_open("PriceTool"):
            tool_name = "CacheTool"

        with span(trace_id, node, parent_span_id, attributes={
            "tool_name": tool_name,
            "prompt_id": "prompt://agent/planner@v1",
            "model": settings.model,
            "retry_count": 0,
            "budget_usd": settings.budget_usd,
            "over_budget": False,
        }) as (node_span_id, attrs):
            idempotency_key = make_idempotency_key(trace_id, node, 1)
            attrs["idempotency_key"] = idempotency_key

            async def call_tool():
                tool = TOOLS[tool_name]
                return await tool.invoke(query, context)

            try:
                result: ToolResult = await execute_with_policies(call_tool)
                if result.ok:
                    circuit_breaker.record_success(tool_name)
                    context[node] = result.value
                    # Rerank for search
                    if node == "search":
                        candidates = (result.value or {}).get("candidates", [])
                        context["search_top"] = rerank_top_one(candidates)
                    return True, node_span_id
                else:
                    circuit_breaker.record_failure(tool_name)
                    # Try ReAct fallback once
                    recovered = await react_recover(query, context)
                    if recovered.ok:
                        context[node] = recovered.value
                        return True, node_span_id
                    return False, node_span_id
            except Exception:
                circuit_breaker.record_failure(tool_name)
                # Try ReAct fallback once
                recovered = await react_recover(query, context)
                if recovered.ok:
                    context[node] = recovered.value
                    return True, node_span_id
                return False, node_span_id

    # Root span
    with span(trace_id, "plan_execute", None, attributes={
        "prompt_id": "prompt://agent/planner@v1",
        "model": settings.model,
        "budget_usd": settings.budget_usd,
        "over_budget": False,
    }) as (root_span_id, _):
        ok, s1 = await run_node("search", root_span_id)
        if not ok:
            return {"status": "error", "message": "search_failed", "context": context}
        ok, s2 = await run_node("price", s1)
        if not ok:
            return {"status": "degraded", "message": "price_failed", "context": context}
        return {"status": "success", "context": context}


