"""Multi-agent research graph using LangGraph + Anthropic tools."""

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from anthropic import Anthropic

SYSTEM_PROMPT = """You are the lead research orchestrator.
Plan work, spawn workers, and stop when the goal is met or budgets exhaust."""

WORKER_INSTRUCTIONS = """You are a research worker. Search, extract findings,
and append structured notes to the scratchpad. Never invent citations."""


@tool
def web_search(query: str) -> str:
    """Search the public web for the query and return snippets."""
    return f"results for {query}"


def build_graph():
    graph = StateGraph(dict)
    graph.add_node("lead", lead_node)
    graph.add_node("worker", worker_node)
    graph.add_node("judge", judge_node)
    graph.add_edge(START, "lead")
    graph.add_conditional_edges("lead", route_next)
    graph.add_edge("worker", "judge")
    graph.add_edge("judge", "lead")
    graph.add_edge("lead", END)
    return graph.compile(checkpointer=True).with_config({"recursion_limit": 12})


def lead_node(state):
    client = Anthropic()
    client.messages.create(
        model="claude-sonnet-4-20250514",
        system=SYSTEM_PROMPT,
        max_tokens=1024,
        tools=[{
            "name": "web_search",
            "description": "Search the web",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }],
        messages=[{"role": "user", "content": state["query"]}],
    )
    return state


def worker_node(state):
    tools = [web_search]
    return {**state, "worker_outputs": state.get("worker_outputs", []) + ["ok"]}


def judge_node(state):
    return state


def route_next(state):
    if state.get("turns", 0) >= 8:
        return END
    return "worker"
