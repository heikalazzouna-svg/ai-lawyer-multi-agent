from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, unique=True, index=True, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # In a real app, this would tie to a User model
    user_id = Column(String, index=True, default="anonymous")
    
    # A session can have many messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    role = Column(String, index=True) # "user" or "ai"
    content = Column(Text)
    
    # Metadata for AI messages
    agent_name = Column(String, nullable=True) 
    citations_verified = Column(Boolean, default=False)

    session = relationship("ChatSession", back_populates="messages")
