import os
import time
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM with Groq
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))

# SIMPLEST POSSIBLE STATE
class AgentState(TypedDict):
    idea: str
    user_name: str
    ideal_customer: str
    problem_solved: str
    search_results: str
    analysis: str
    is_new_chat: bool
    messages: List[str]

def web_research_node(state: AgentState):
    time.sleep(1)
    return {"search_results": f"Research results for {state['idea']}"}

def llm_agent_node(state: AgentState):
    prompt = f"Analyze feasibility of {state['idea']} for {state['ideal_customer']}. Provide 6 sections in HTML-like structure: 1. Idea Fit, 2. Competitors, 3. Opportunity, 4. Score, 5. Targeting, 6. Next Step. Be detailed."
    response = llm.invoke(prompt)
    return {"analysis": response.content}

# Create Graph
workflow = StateGraph(AgentState)
workflow.add_node("research", web_research_node)
workflow.add_node("analyzer", llm_agent_node)
workflow.set_entry_point("research")
workflow.add_edge("research", "analyzer")
workflow.add_edge("analyzer", END)

app = workflow.compile()
