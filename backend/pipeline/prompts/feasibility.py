def get_feasibility_prompt(idea: str, ideal_customer: str, search_results: str) -> str:
    return (
        f"Analyze feasibility of '{idea}' for '{ideal_customer}'.\n\n"
        f"We have scraped recent market research and competitor data from the web:\n"
        f"=== WEB DATA ===\n"
        f"{search_results}\n"
        f"================\n\n"
        "Provide the response as a single valid JSON object with EXACTLY these 7 keys:\n"
        '{\n'
        '  "chain_of_thought": "Explain your step-by-step reasoning based explicitly on the WEB DATA provided above. Analyze market gaps, competitor strengths/weaknesses, and technical/market viability.",\n'
        '  "idea_fit": "Analyze how well this idea solves the target problem based on the market landscape...",\n'
        '  "competitors": "List and analyze the specific competitors found in the web data...",\n'
        '  "opportunity": "Identify the specific market gaps or opportunities mentioned or inferred from the data...",\n'
        '  "score": "Give a feasibility score out of 100 based on the analysis (e.g. 75/100)...",\n'
        '  "targeting": "Recommend exact customer segments to target based on the research...",\n'
        '  "next_step": "Provide actionable next steps to validate or build the product..."\n'
        '}\n\n'
        "Do not include any markdown formatting like ```json, just return the raw valid JSON object. Your entire analysis MUST be grounded in the provided web data."
    )
