from sentence_transformers import SentenceTransformer, util

print("  [🔧] Loading router model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("  [✅] Router model loaded!")

AGENT_DESCRIPTIONS = {
    "admissions": """
        college admission eligibility cutoff marks cutoff rank
        apply joining fees lateral entry NRI OCI foreign students SAT TNEA
        HSC qualifications documents required regulation minimum marks
        category OC BC MBC SC BCM branch wise rank cutoff 2025 community wise
        courses offered syllabus curriculum subjects semester credits
        BE BTech ME undergraduate postgraduate programme
        computer science engineering information technology
        artificial intelligence data science AI DS AI ML electronics
        communication ECE electrical EEE mechanical civil biomedical
        mechatronics VLSI advanced communication technology
        computer science business systems
        what courses are offered what programmes what branches
        syllabus of AI DS syllabus of CSE syllabus of IT
        semester wise subjects list of subjects curriculum structure
    """,

    "placements": """
        placement placements job salary package LPA companies
        recruiting internship training aptitude soft skills
        mock interview hired offer letter TCS Infosys Wipro
        Amazon Microsoft placement statistics percentage
        highest salary average package placement record placement season
        career outcomes job offers recruitment drive campus placement
        how many students got placed placement 2024 2025
    """,

    "career_guidance": """
        career future scope after graduation job roles prospects
        higher studies MS MBA GATE GRE study abroad
        which course should I choose what to do after engineering
        industry trends salary range career path career advice
        what skills are needed for job market
        career options for graduates recommend career
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