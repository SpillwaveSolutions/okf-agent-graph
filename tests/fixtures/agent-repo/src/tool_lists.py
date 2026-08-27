"""Tool bindings whose list bodies are not a single identifier."""

from langchain_core.tools import StructuredTool


def bind():
    tools = [
        {
            "name": "lookup",
            "description": "Look something up",
            "input_schema": {"type": "object"},
        }
    ]
    StructuredTool.from_function(lookup)
    input_schema = {"type": "object"}
    return tools


def lookup(query: str) -> str:
    return query
