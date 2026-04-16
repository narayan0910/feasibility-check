from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from api.dependencies import (
    get_db
)
from models import ChatSession, AgentStateModel, FeasibilityReport
from pipeline.graph import app as langgraph_app
import json

router = APIRouter()


class IdeaInput(BaseModel):
    idea: str
    user_name: str
    ideal_customer: str
    problem_solved: str
    authorId: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    analysis: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(input_data: IdeaInput, db: Session = Depends(get_db)):
    print("--- INCOMING REQUEST ---")
    print(f"Idea: {input_data.idea}")

    is_new_chat = True
    conv_id = input_data.conversation_id
    
    original_idea = input_data.idea
    problem_solved = input_data.problem_solved
    ideal_customer = input_data.ideal_customer
    current_message = input_data.idea

    initial_analysis = ""
    if conv_id:
        existing = db.query(ChatSession).filter(ChatSession.conversation_id == conv_id).order_by(ChatSession.timestamp.asc()).first()
        state_model = db.query(AgentStateModel).filter(AgentStateModel.conversation_id == conv_id).first()
        
        if existing:
            is_new_chat = False
            original_idea = existing.idea or original_idea
            problem_solved = existing.what_problem_it_solves or problem_solved
            ideal_customer = existing.ideal_customer or ideal_customer
            current_message = input_data.idea  # The user's newest reply
            
        if state_model:
            initial_analysis = state_model.analysis or ""
    else:
        conv_id = str(uuid.uuid4())

    initial_state = {
        "idea": original_idea,
        "user_name": input_data.user_name,
        "ideal_customer": ideal_customer,
        "problem_solved": problem_solved,
        "messages": [],
        "search_results": "",
        "analysis": initial_analysis,
        "is_new_chat": is_new_chat,
        "conversation_id": conv_id,
        "conversation_history": [],
        "optimized_query": "",
        "optimized_queries": [],
        "current_message": current_message
    }

    result = await langgraph_app.ainvoke(initial_state)

    new_entry = ChatSession(
        authorId=input_data.authorId,
        conversation_id=conv_id,
        user_name=input_data.user_name,
        idea=original_idea,
        what_problem_it_solves=problem_solved,
        ideal_customer=ideal_customer,
        human_message=current_message,
        ai_message=result.get("analysis", "Error in analysis"),
    )
    db.add(new_entry)
    
    # ── Upsert the State record ──
    state_model = db.query(AgentStateModel).filter(AgentStateModel.conversation_id == conv_id).first()
    if not state_model:
        state_model = AgentStateModel(conversation_id=conv_id)
        db.add(state_model)
    
    state_model.optimized_query = result.get("optimized_query", state_model.optimized_query)
    state_model.search_results = result.get("search_results", state_model.search_results)
    state_model.analysis = result.get("analysis", state_model.analysis)

    # ── Try parsing and storing the JSON feasibility report ──
    raw_analysis = result.get("analysis", "")
    if raw_analysis and not is_new_chat:
        try:
            # We expect raw json string. Sometimes LLMs sneak in ```json markers
            clean_json = raw_analysis.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Upsert into feasibility_reports
            report = db.query(FeasibilityReport).filter(FeasibilityReport.conversation_id == conv_id).first()
            if not report:
                report = FeasibilityReport(conversation_id=conv_id)
                db.add(report)
                
            report.chain_of_thought = data.get("chain_of_thought")
            report.idea_fit = data.get("idea_fit")
            report.competitors = data.get("competitors")
            report.opportunity = data.get("opportunity")
            report.score = data.get("score")
            report.targeting = data.get("targeting")
            report.next_step = data.get("next_step")
            
        except json.JSONDecodeError:
            print("Warning: LLM analysis output wasn't valid JSON. Could not parse to FeasibilityReport.")

    db.commit()

    return ChatResponse(
        response="Analysis Complete" if not is_new_chat else "Researching your idea...",
        conversation_id=conv_id,
        analysis=result.get("analysis"),
    )
