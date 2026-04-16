from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from api.dependencies import get_db
from models import ChatSession
from pipeline.graph import app as langgraph_app

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

    if conv_id:
        existing = db.query(ChatSession).filter(ChatSession.conversation_id == conv_id).first()
        if existing:
            is_new_chat = False
    else:
        conv_id = str(uuid.uuid4())

    initial_state = {
        "idea": input_data.idea,
        "user_name": input_data.user_name,
        "ideal_customer": input_data.ideal_customer,
        "problem_solved": input_data.problem_solved,
        "messages": [],
        "search_results": "",
        "analysis": "",
        "is_new_chat": is_new_chat,
    }

    result = langgraph_app.invoke(initial_state)

    new_entry = ChatSession(
        authorId=input_data.authorId,
        conversation_id=conv_id,
        user_name=input_data.user_name,
        idea=input_data.idea,
        what_problem_it_solves=input_data.problem_solved,
        ideal_customer=input_data.ideal_customer,
        human_message=input_data.idea,
        ai_message=result.get("analysis", "Error in analysis"),
    )
    db.add(new_entry)
    db.commit()

    return ChatResponse(
        response="Analysis Complete" if not is_new_chat else "Researching your idea...",
        conversation_id=conv_id,
        analysis=result.get("analysis"),
    )
