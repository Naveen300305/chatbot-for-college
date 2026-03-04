import os
from dotenv import load_dotenv
from agent_router import route
from agents.admissions_agent import AdmissionsAgent
from agents.placements_agent import PlacementsAgent
from agents.career_agent import CareerAgent

load_dotenv()

# ─────────────────────────────────────────
# Load all 3 agents once
# ─────────────────────────────────────────
print("\n" + "="*55)
print("Loading all agents...")
print("="*55)

agents = {
    "admissions"      : AdmissionsAgent(),      
    "placements"      : PlacementsAgent(),        
    "career_guidance" : CareerAgent()           
}

print("\n✅ All agents ready!\n")

# ─────────────────────────────────────────
# Test questions
# ─────────────────────────────────────────
test_questions = [
    "What is the cutoff for CSE for OC category?",
    "Which companies hire from CIT?",
    "What career can I have after ECE?",
]

print("="*55)
print("FULL PIPELINE TEST")
print("="*55)

for question in test_questions:
    print(f"\n🧑 Question: {question}")
    print("-"*55)

    # Step 1: Route
    route_result = route(question)
    agent_name   = route_result["agent"]
    confidence   = route_result["confidence"]
    print(f"🔀 Routed to : {agent_name} (confidence: {confidence})")

    # Step 2: Get answer from correct agent
    result = agents[agent_name].answer(question)

    print(f"📄 Sources   : {result['sources']}")
    print(f"🤖 Answer    :\n{result['answer']}")
    print("="*55)