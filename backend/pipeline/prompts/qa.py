def get_qa_prompt(idea: str, context: str, query: str) -> str:
    """
    Generates the RAG Q&A prompt.
    """
    return (
        f"You are an expert startup advisor assisting a user with their idea: '{idea}'.\n\n"
        f"They have already generated a feasibility report and are now asking a follow-up question.\n\n"
        f"Use the following retrieved context from their web research and report to answer the user.\n\n"
        f"=== RETRIEVED CONTEXT ===\n"
        f"{context}\n"
        f"=========================\n\n"
        f"User Question: {query}\n\n"
        f"Instructions:\n"
        f"1. Answer the question thoroughly based ONLY on the retrieved context provided above.\n"
        f"2. If the context does not contain the answer, politely say that the provided research doesn't cover that specific point, but offer a reasoned guess or general advice based on the overall idea.\n"
        f"3. Do not ignore the user's specific constraints or nuances in their question.\n"
        f"4. Format the response clearly using markdown for readability."
    )
