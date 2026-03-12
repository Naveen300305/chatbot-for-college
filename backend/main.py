# backend/main.py
import os
import sys
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent classes
from agents.admissions_agent import AdmissionsAgent
from agents.placements_agent import PlacementsAgent
from agents.career_agent import CareerAgent
from agent_router import route

# Import database models
from database import SessionLocal, Conversation

# Create FastAPI app
app = FastAPI(title="CIT College Assistant")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents (same as Streamlit)
agents = None

def load_agents():
    """Load all agent instances"""
    return {
        "admissions": AdmissionsAgent(),
        "placements": PlacementsAgent(),
        "career_guidance": CareerAgent()
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load agents once
    global agents
    print("Loading agents...")
    agents = load_agents()
    print("Agents loaded successfully")
    yield
    # Shutdown: Cleanup
    print("Shutting down gracefully")

app.router.lifespan_context = lifespan

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "agents_loaded": agents is not None}

# WebSocket endpoint for text conversation
@app.websocket("/ws/chat")
async def chat_conversation(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    db = SessionLocal()
    start_time = datetime.utcnow()

    print(f"Client {session_id} connected")

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive" and "text" in message:
                try:
                    import json
                    data = json.loads(message["text"])

                    if data.get("type") == "text_query":
                        user_text = data.get("content", "").strip()
                        if not user_text:
                            continue
                    else:
                        continue
                except json.JSONDecodeError:
                    continue
            else:
                continue

            try:
                # Route to correct agent
                route_result = route(user_text)
                agent_name = route_result["agent"]
                confidence = route_result["confidence"]

                await websocket.send_json({
                    "type": "agent_selected",
                    "agent": agent_name,
                    "confidence": round(confidence * 100, 1)
                })

                print(f"[{session_id}] Routed to: {agent_name} ({confidence*100:.2f}% confidence)")

                if agents is None:
                    raise Exception("Agents not loaded")

                agent = agents[agent_name]
                full_response = ""
                sources = []

                async for text_chunk, chunk_sources in agent.answer_stream_async(
                    user_text,
                    chat_history=[]
                ):
                    if text_chunk:
                        sources = chunk_sources
                        full_response += text_chunk
                        await websocket.send_json({
                            "type": "text_chunk",
                            "content": text_chunk
                        })

                await websocket.send_json({
                    "type": "complete",
                    "sources": sources,
                    "agent": agent_name
                })

                # Save to database
                duration = (datetime.utcnow() - start_time).total_seconds()
                conversation = Conversation(
                    session_id=session_id,
                    user_transcription=user_text,
                    agent_selected=agent_name,
                    agent_confidence=confidence,
                    response_text=full_response,
                    duration_seconds=duration
                )
                db.add(conversation)
                db.commit()

            except Exception as e:
                print(f"[{session_id}] Error: {str(e)}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": "Processing failed. Please try again."
                })

    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    except Exception as e:
        print(f"WebSocket error for {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# API endpoints for session history
@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve all conversations from a session"""
    db = SessionLocal()
    conversations = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).all()
    db.close()
    return {
        "session_id": session_id,
        "conversations": [
            {
                "user_text": c.user_transcription,
                "agent": c.agent_selected,
                "confidence": c.agent_confidence,
                "response": c.response_text,
                "sources": c.sources,
                "timestamp": c.created_at.isoformat() if c.created_at else None
            }
            for c in conversations
        ]
    }

@app.get("/api/stats/{session_id}")
async def get_session_stats(session_id: str):
    """Get statistics for a session"""
    db = SessionLocal()
    conversations = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).all()

    agent_counts = {}
    total_duration = 0

    for conv in conversations:
        agent_counts[conv.agent_selected] = agent_counts.get(conv.agent_selected, 0) + 1
        total_duration += conv.duration_seconds or 0

    db.close()
    return {
        "total_questions": len(conversations),
        "agents_used": agent_counts,
        "total_duration_seconds": total_duration
    }

# ─── Gemini Live: Ephemeral Token ───
@app.post("/api/ephemeral-token")
async def get_ephemeral_token():
    """Generate an ephemeral token for client-side Gemini Live API access"""
    try:
        from gemini_live import create_ephemeral_token
        token_data = create_ephemeral_token()
        return token_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ─── Gemini Live: RAG Query ───
class RAGQueryRequest(BaseModel):
    query: str
    category: Optional[str] = None

@app.post("/api/rag-query")
async def rag_query(request: RAGQueryRequest):
    """Query the ChromaDB knowledge base — used by Gemini function calling"""
    try:
        if agents is None:
            return {"error": "Agents not loaded"}

        # Auto-route to the best agent if category not specified
        if request.category and request.category in agents:
            agent_name = request.category
        else:
            route_result = route(request.query)
            agent_name = route_result["agent"]

        agent = agents[agent_name]

        # Query ChromaDB
        results = agent.collection.query(
            query_texts=[request.query],
            n_results=3
        )

        # Merge mandatory + semantic chunks
        m_docs, m_metas = agent._get_mandatory_chunks(request.query)
        chunks, metas = agent._merge_chunks(
            m_docs, m_metas,
            results["documents"][0], results["metadatas"][0],
            request.query
        )

        # Compact context — shorter = faster for model to process
        context = "\n---\n".join(chunks[:3])

        sources = list(set([
            meta.get("topic", "unknown") for meta in metas
        ]))

        return {
            "context": context,
            "sources": sources,
            "agent": agent_name
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)