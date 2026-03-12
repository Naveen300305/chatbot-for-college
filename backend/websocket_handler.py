# backend/websocket_handler.py
import uuid
import json
from database import SessionLocal, Conversation
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from agent_router import route
from agents.admissions_agent import AdmissionsAgent
from agents.placements_agent import PlacementsAgent
from agents.career_agent import CareerAgent

agents = {
    "admissions": AdmissionsAgent(),
    "placements": PlacementsAgent(),
    "career_guidance": CareerAgent()
}

async def chat_conversation(websocket: WebSocket): 
    await websocket.accept()

    session_id = str(uuid.uuid4())
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.receive" and "text" in message:
                try:
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
                print(f"Error processing: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": "Processing failed. Please try again."
                })

    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    finally:
        db.close()