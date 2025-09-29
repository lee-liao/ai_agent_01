from typing import Literal


def route(query: str, node: Literal["search", "price"]) -> str:
    """Simple router: if query contains 'price' route to PriceTool, else SearchTool.
    For node sequencing we still respect the plan node type.
    """
    q = (query or "").lower()
    if node == "search":
        return "SearchTool"
    if node == "price":
        if "price" in q:
            return "PriceTool"
        return "SearchTool"
    return "SearchTool"


