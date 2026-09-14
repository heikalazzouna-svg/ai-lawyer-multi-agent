"""
Test script to verify Database Persistence (SQLAlchemy).
Run this to ensure the database initializes correctly and can store chat sessions.
"""
import os
from database import Base, engine, SessionLocal
from models import ChatSession, ChatMessage

def test():
    print("\n--- Testing Database Persistence ---")
    
    # 1. Initialize Tables
    print("[1] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Insert Dummy Data
    print("[2] Opening session and writing data...")
    db = SessionLocal()
    
    session = ChatSession(user_id="test_user")
    db.add(session)
    db.commit()
    db.refresh(session)
    
    msg_user = ChatMessage(session_id=session.id, role="user", content="Hello AI!")
    msg_ai = ChatMessage(session_id=session.id, role="ai", content="Hello Human!", agent_name="Assistant")
    
    db.add_all([msg_user, msg_ai])
    db.commit()
    
    # 3. Read Data
    print("[3] Reading data back from the database...")
    saved_session = db.query(ChatSession).filter_by(id=session.id).first()
    
    assert saved_session is not None, "Session was not saved!"
    assert len(saved_session.messages) == 2, "Messages were not saved!"
    
    for m in saved_session.messages:
        print(f"  [{m.role.upper()}] {m.content}")
        
    print("\n✅ Database Persistence is working perfectly!")
    
    # Cleanup dummy data
    db.delete(saved_session)
    db.commit()
    db.close()

if __name__ == "__main__":
    test()
