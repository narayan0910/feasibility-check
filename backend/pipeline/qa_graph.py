"""
pipeline/qa_graph.py
────────────────────
LangGraph pipeline for Q&A over an existing feasibility conversation.
This flow reuses the shared AgentState shape used by /chat and adds QA traceability.
"""

from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END

from pipeline.state import AgentState
from pipeline.prompts.qa import get_qa_prompt
from rag.retriever import retrieve_context
from core.llm_factory import get_llm


def _append_trace(state: AgentState, step: str, message: str, metadata: dict | None = None) -> list[dict]:
    trace = list(state.get("trace", []))
    trace.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "message": message,
            "metadata": metadata or {},
        }
    )
    return trace


def qa_load_state_node(state: AgentState) -> dict:
    print("--- QA NODE: qa_load_state_node ---")
    trace = _append_trace(
        state,
        "qa_load_state",
        "Loaded persisted conversation state and history for QA.",
        {
            "conversation_id": state.get("conversation_id"),
            "history_turns": len(state.get("conversation_history", [])),
            "has_analysis": bool(state.get("analysis")),
            "has_search_results": bool(state.get("search_results")),
        },
    )
    return {"trace": trace}


def qa_modify_query_node(state: AgentState) -> dict:
    print("--- QA NODE: qa_modify_query_node ---")
    original_question = state.get("question", "").strip()
    idea = state.get("idea", "")
    problem_solved = state.get("problem_solved", "")

    if not original_question:
        trace = _append_trace(
            state,
            "qa_modify_query",
            "Skipped query modification because question was empty.",
        )
        return {"qa_retrieval_query": "", "trace": trace}

    history = state.get("conversation_history", [])[-4:]
    history_str = "\n".join(
        [f"User: {h.get('user', '')}\nAI: {h.get('ai', '')}" for h in history]
    )

    llm = get_llm(temperature=0.2)
    rewrite_prompt = (
        "You rewrite follow-up startup questions into standalone retrieval queries.\n"
        "Use startup context to disambiguate pronouns/short phrases.\n"
        "Do not invent facts. Keep it concise and explicit.\n"
        "Return ONLY the rewritten query text, no markdown.\n\n"
        f"Startup idea: {idea}\n"
        f"Problem solved: {problem_solved}\n"
        f"Recent conversation:\n{history_str}\n\n"
        f"User follow-up question: {original_question}\n\n"
        "Example:\n"
        "Input: will it work in india\n"
        "Output: will the smart mirror startup work in india\n"
    )

    try:
        rewritten = (llm.invoke(rewrite_prompt).content or "").strip().strip('"')
    except Exception:
        rewritten = ""

    if not rewritten:
        rewritten = f"For the startup idea '{idea}', {original_question}".strip()

    trace = _append_trace(
        state,
        "qa_modify_query",
        "Rewrote user question into standalone retrieval query.",
        {
            "original_question": original_question,
            "rewritten_query": rewritten,
        },
    )

    return {
        "qa_retrieval_query": rewritten,
        "trace": trace,
    }


def qa_retrieve_context_node(state: AgentState) -> dict:
    print("--- QA NODE: qa_retrieve_context_node ---")
    question = state.get("question", "").strip()
    retrieval_query = state.get("qa_retrieval_query", "").strip() or question
    conv_id = state.get("conversation_id", "")

    print(f"  [QA] Original question: {question}")
    print(f"  [QA] Retrieval query : {retrieval_query}")

    context, chunks = retrieve_context(conversation_id=conv_id, query=retrieval_query, top_k=5)

    # Fallback context to ensure QA can still respond even if vector retrieval is empty.
    if not chunks:
        fallback_context = (
            f"[Persisted analysis]\n{state.get('analysis', '')}\n\n"
            f"[Persisted web research]\n{state.get('search_results', '')}"
        ).strip()
        context = fallback_context or "No relevant context found."
        print("  [QA] No vector chunks found, using persisted fallback context.")

    trace = _append_trace(
        state,
        "qa_retrieve_context",
        "Retrieved RAG context for the user question.",
        {
            "question": question,
            "retrieval_query": retrieval_query,
            "top_chunks": len(chunks),
            "used_fallback": len(chunks) == 0,
        },
    )

    return {
        "rag_context": context,
        "top_chunks": chunks,
        "trace": trace,
    }


def qa_generate_answer_node(state: AgentState) -> dict:
    print("--- QA NODE: qa_generate_answer_node ---")

    question = state.get("question", "")
    idea = state.get("idea", "your startup idea")
    context = state.get("rag_context", "No relevant context found.")

    llm = get_llm()
    prompt = get_qa_prompt(idea=idea, context=context, query=question)
    response = llm.invoke(prompt)

    trace = _append_trace(
        state,
        "qa_generate_answer",
        "Generated final QA response with LLM.",
        {
            "model_response_chars": len(response.content or ""),
        },
    )

    return {
        "qa_answer": response.content,
        "trace": trace,
    }


qa_workflow = StateGraph(AgentState)
qa_workflow.add_node("qa_load_state", qa_load_state_node)
qa_workflow.add_node("qa_modify_query", qa_modify_query_node)
qa_workflow.add_node("qa_retrieve_context", qa_retrieve_context_node)
qa_workflow.add_node("qa_generate_answer", qa_generate_answer_node)

qa_workflow.add_edge(START, "qa_load_state")
qa_workflow.add_edge("qa_load_state", "qa_modify_query")
qa_workflow.add_edge("qa_modify_query", "qa_retrieve_context")
qa_workflow.add_edge("qa_retrieve_context", "qa_generate_answer")
qa_workflow.add_edge("qa_generate_answer", END)

qa_app = qa_workflow.compile()


def get_qa_graph_mermaid() -> str:
    """Returns a Mermaid diagram for QA graph visualization."""
    try:
        return qa_app.get_graph().draw_mermaid()
    except Exception:
        # Fallback static graph in case runtime graph rendering is unavailable.
        return (
            "graph TD\n"
            "    START --> qa_load_state\n"
            "    qa_load_state --> qa_modify_query\n"
            "    qa_modify_query --> qa_retrieve_context\n"
            "    qa_retrieve_context --> qa_generate_answer\n"
            "    qa_generate_answer --> END"
        )
