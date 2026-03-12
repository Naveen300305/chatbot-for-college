from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), index=True)
    user_transcription = Column(String(1000))
    agent_selected = Column(String(50))
    agent_confidence = Column(Float)
    response_text = Column(String(5000))
    created_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float)

# Initial DB setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)