"""
pipeline/tools.py
─────────────────
All tool functions / node callables used in the LangGraph pipeline.
Add new tools here and wire them into graph.py.
"""

import asyncio
from pipeline.state import AgentState
from pipeline.prompts.feasibility import get_feasibility_prompt
from scraper.web import ddgs_url_scrapper, crawler_service


def web_research_node(state: AgentState) -> dict:
    """
    Tool: Web Research
    Searches duckduckgo for market data and crawls top URLs using crawl4ai.
    """
    idea = state['idea']
    problem_solved = state['problem_solved']
    query = f"{idea} {problem_solved} market competitors"
    
    urls = ddgs_url_scrapper(query)
    
    if not urls:
        return {"search_results": "No relevant data found on the web."}
        
    # Run the async crawler service
    results_text = asyncio.run(crawler_service(urls))
    
    return {"search_results": results_text}


def llm_agent_node(state: AgentState) -> dict:
    """
    Tool: LLM Feasibility Analyser
    Calls the Groq LLM to produce a structured feasibility report.
    """
    from pipeline.graph import llm          # local import avoids circular refs

    prompt = get_feasibility_prompt(
        idea=state['idea'],
        ideal_customer=state['ideal_customer'],
        search_results=state['search_results']
    )
    response = llm.invoke(prompt)
    return {"analysis": response.content}
