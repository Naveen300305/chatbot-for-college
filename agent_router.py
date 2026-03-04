from sentence_transformers import SentenceTransformer, util

print("  [🔧] Loading router model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("  [✅] Router model loaded!")

AGENT_DESCRIPTIONS = {
    "admissions": """
        college admission eligibility cutoff marks cutoff rank
        apply joining courses offered fees lateral entry NRI OCI
        foreign students SAT scores TNEA HSC qualifications
        documents required BE BTech ME syllabus semesters credits
        regulation minimum marks category OC BC MBC SC BCM
        branch wise rank cutoff 2025 community wise
    """,

    "placements": """
        placement placements job salary package LPA companies
        recruiting internship training aptitude soft skills
        mock interview hired offer letter TCS Infosys Wipro
        Amazon Microsoft placement statistics percentage
        highest salary average package tell me about placements
        placement record placement season career outcomes
        job offers recruitment drive campus placement
    """,

    "career_guidance": """
        career future scope after graduation job roles
        higher studies MS MBA GATE GRE abroad
        skills required recommend which course suits me
        industry trends salary range what to do after
        software developer data scientist engineer
    """
}

# Pre-compute agent embeddings once at startup
AGENT_EMBEDDINGS = {
    agent: model.encode(desc, convert_to_tensor=True)
    for agent, desc in AGENT_DESCRIPTIONS.items()
}


def route(user_message: str) -> dict:
    message_embedding = model.encode(
        user_message,
        convert_to_tensor=True
    )

    scores = {}
    for agent, agent_embedding in AGENT_EMBEDDINGS.items():
        similarity = util.cos_sim(
            message_embedding,
            agent_embedding
        ).item()
        scores[agent] = round(similarity, 4)

    best_agent = max(scores, key=scores.get)
    confidence = scores[best_agent]

    print(f"  [🔀] Scores: {scores}")
    print(f"  [✅] Routing to: {best_agent} (confidence: {confidence})")

    return {
        "agent": best_agent,
        "confidence": confidence,
        "all_scores": scores
    }