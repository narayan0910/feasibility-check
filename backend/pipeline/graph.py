"""
pipeline/graph.py
─────────────────
Builds and compiles the LangGraph StateGraph.
Import `app` from here wherever the pipeline needs to be invoked.
"""

import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from core.config import settings
from pipeline.state import AgentState
from pipeline.tools import web_research_node, llm_agent_node


# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=settings.OPENAI_API_KEY,
    temperature=0.7,
)

# ── Graph ─────────────────────────────────────────────────────────────────────
workflow = StateGraph(AgentState)

workflow.add_node("research", web_research_node)
workflow.add_node("analyzer", llm_agent_node)

workflow.set_entry_point("research")
workflow.add_edge("research", "analyzer")
workflow.add_edge("analyzer", END)

app = workflow.compile()
