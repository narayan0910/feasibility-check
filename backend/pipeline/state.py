"""
pipeline/state.py
─────────────────
Shared TypedDict that defines the LangGraph agent state.
"""

from typing import TypedDict, List


class AgentState(TypedDict):
    idea: str
    user_name: str
    ideal_customer: str
    problem_solved: str
    search_results: str
    analysis: str
    is_new_chat: bool
    messages: List[str]
