import os
from datetime import datetime, timedelta, timezone
from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-2.5-flash-native-audio-latest"

SYSTEM_INSTRUCTION = """You are a voice assistant for Chennai Institute of Technology (CIT), Chennai, India.
Answer briefly about admissions, courses, placements, career guidance, eligibility, cutoffs, and campus life.
Call query_college_info ONLY for specific data like cutoffs, stats, eligibility, or syllabus — NOT for greetings or general chat.
Keep answers short (2-3 sentences) since you are speaking aloud. Refer to the college as CIT."""

QUERY_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="query_college_info",
            description="Search the CIT college knowledge base for information about admissions, placements, career guidance, courses, eligibility, cutoffs, syllabus, recruiting companies, training methods, and more.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(
                        type="STRING",
                        description="The search query to find relevant information in the college knowledge base",
                    ),
                    "category": types.Schema(
                        type="STRING",
                        enum=["admissions", "placements", "career_guidance"],
                        description="Optional category to narrow the search to a specific knowledge domain",
                    ),
                },
                required=["query"],
            ),
        )
    ]
)


def create_ephemeral_token() -> dict:
    """Generate config for client-side Gemini Live API access.
    Uses the API key directly (ephemeral tokens can be added later for production).
    """
    return {
        "token": GOOGLE_API_KEY,
        "model": MODEL,
        "config": {
            "model": f"models/{MODEL}",
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Aoede"
                        }
                    }
                }
            },
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "tools": [
                {
                    "functionDeclarations": [
                        {
                            "name": "query_college_info",
                            "description": "Look up specific CIT data: cutoffs, placement stats, eligibility, syllabus, or recruiting companies.",
                            "parameters": {
                                "type": "OBJECT",
                                "properties": {
                                    "query": {
                                        "type": "STRING",
                                        "description": "Search query"
                                    },
                                    "category": {
                                        "type": "STRING",
                                        "enum": ["admissions", "placements", "career_guidance"],
                                        "description": "Knowledge domain"
                                    }
                                },
                                "required": ["query", "category"]
                            }
                        }
                    ]
                }
            ],
            "outputAudioTranscription": {}
        }
    }
