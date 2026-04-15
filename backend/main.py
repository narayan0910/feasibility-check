from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from database import init_db, get_db
from models import ChatSession
from langgraph_engine import app as langgraph_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Initialize DB
init_db()

app = FastAPI(title="Feasibility Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (models and IdeaInput stay the same)

# MOUNT FRONTEND
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(input_data: IdeaInput, db: Session = Depends(get_db)):
    print(f"--- INCOMING REQUEST ---")
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
        "is_new_chat": is_new_chat
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
        ai_message=result.get("analysis", "Error in analysis")
    )
    db.add(new_entry)
    db.commit()

    return ChatResponse(
        response="Analysis Complete" if not is_new_chat else "Researching your idea...",
        conversation_id=conv_id,
        analysis=result.get("analysis")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)
