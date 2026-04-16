import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    authorId = Column(String, index=True)
    conversation_id = Column(String, index=True)
    user_name = Column(String)
    idea = Column(Text)
    what_problem_it_solves = Column(Text)
    ideal_customer = Column(Text)
    human_message = Column(Text)
    ai_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
