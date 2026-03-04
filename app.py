import streamlit as st
import os
import time
from dotenv import load_dotenv
from agent_router import route
from agents.admissions_agent import AdmissionsAgent
from agents.placements_agent import PlacementsAgent
from agents.career_agent import CareerAgent

load_dotenv()

# ─────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────
st.set_page_config(
    page_title="CIT Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0f1117;
    }

    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #1e3a5f, #2d5a8e);
        padding: 15px 20px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        color: white;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    .bot-message {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 15px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        color: #e0e0e0;
        max-width: 85%;
        border-left: 3px solid #4a9eff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* Agent badge */
    .agent-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        margin-bottom: 8px;
    }

    .badge-admissions {
        background-color: #1e5f3a;
        color: #4cff91;
    }

    .badge-placements {
        background-color: #5f3a1e;
        color: #ffb74d;
    }

    .badge-career {
        background-color: #3a1e5f;
        color: #ce93d8;
    }

    /* Source tags */
    .source-tag {
        display: inline-block;
        background-color: #1e2a3a;
        color: #7eb3ff;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 11px;
        margin: 2px;
        border: 1px solid #2a3a4a;
    }

    /* Follow-up buttons */
    .stButton button {
        background-color: #1e2a3a;
        color: #7eb3ff;
        border: 1px solid #2a3a4a;
        border-radius: 12px;
        padding: 5px 15px;
        font-size: 13px;
        transition: all 0.2s;
        width: 100%;
        text-align: left;
    }

    .stButton button:hover {
        background-color: #2a3a4a;
        border-color: #4a9eff;
        color: white;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #0a0e17;
    }

    /* Stats card */
    .stats-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2a3a4a;
        margin: 8px 0;
        text-align: center;
    }

    /* Input box */
    .stChatInput input {
        background-color: #1a1a2e;
        color: white;
        border: 1px solid #2a3a4a;
        border-radius: 12px;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f, #0f1117);
        padding: 20px;
        border-radius: 16px;
        border-bottom: 2px solid #4a9eff;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Load Agents (cached so loads only once)
# ─────────────────────────────────────────
@st.cache_resource
def load_agents():
    agents = {
        "admissions"      : AdmissionsAgent(),
        "placements"      : PlacementsAgent(),
        "career_guidance" : CareerAgent()
    }
    return agents


# ─────────────────────────────────────────
# Agent Display Info
# ─────────────────────────────────────────
AGENT_INFO = {
    "admissions": {
        "label"  : "🎓 Admissions Agent",
        "badge"  : "badge-admissions",
        "color"  : "#4cff91",
        "icon"   : "🎓"
    },
    "placements": {
        "label"  : "💼 Placements Agent",
        "badge"  : "badge-placements",
        "color"  : "#ffb74d",
        "icon"   : "💼"
    },
    "career_guidance": {
        "label"  : "🚀 Career Guidance Agent",
        "badge"  : "badge-career",
        "color"  : "#ce93d8",
        "icon"   : "🚀"
    }
}


# ─────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────
if "chat_history"     not in st.session_state:
    st.session_state.chat_history = []
if "followup_questions" not in st.session_state:
    st.session_state.followup_questions = []
if "total_questions"  not in st.session_state:
    st.session_state.total_questions = 0
if "agent_counts"     not in st.session_state:
    st.session_state.agent_counts = {
        "admissions": 0,
        "placements": 0,
        "career_guidance": 0
    }
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ─────────────────────────────────────────
# Load agents
# ─────────────────────────────────────────
with st.spinner("🔧 Loading CIT Assistant..."):
    agents = load_agents()


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 CIT Assistant")
    st.markdown("*Chennai Institute of Technology*")
    st.divider()

    # Agent Status
    st.markdown("### 🤖 Agent Status")
    for agent_key, info in AGENT_INFO.items():
        st.markdown(
            f"<div style='padding:8px; background:#1a1a2e; "
            f"border-radius:8px; margin:4px 0; border-left: 3px solid {info['color']};'>"
            f"{info['icon']} {info['label'].split(' ', 1)[1]}"
            f"<span style='float:right; color:#4cff91;'>● Online</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # Session Stats
    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions", st.session_state.total_questions)
    with col2:
        most_used = max(
            st.session_state.agent_counts,
            key=st.session_state.agent_counts.get
        )
        st.metric("Top Agent", AGENT_INFO[most_used]["icon"])

    # Agent usage breakdown
    for agent_key, info in AGENT_INFO.items():
        count = st.session_state.agent_counts[agent_key]
        total = st.session_state.total_questions or 1
        pct   = int((count / total) * 100)
        st.markdown(
            f"<div style='margin:4px 0; font-size:13px;'>"
            f"{info['icon']} {pct}%"
            f"<div style='background:#1a1a2e; border-radius:4px; height:6px; margin-top:3px;'>"
            f"<div style='background:{info['color']}; width:{pct}%; height:6px; border-radius:4px;'></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    st.divider()

    # Sample Questions
    st.markdown("### 💡 Try Asking")
    sample_questions = [
        "What is the CSE cutoff for OC?",
        "Which companies hire from CIT?",
        "What career after ECE?",
        "Lateral entry eligibility?",
        "Highest salary package?",
        "Should I do MS or MBA?"
    ]
    for q in sample_questions:
        if st.button(q, key=f"sample_{q}"):
            st.session_state.pending_question = q
            st.rerun()

    st.divider()

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.followup_questions = []
        st.session_state.total_questions = 0
        st.session_state.agent_counts = {
            "admissions": 0,
            "placements": 0,
            "career_guidance": 0
        }
        st.rerun()


# ─────────────────────────────────────────
# MAIN AREA — Header
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin:0;">🎓 CIT Smart Assistant</h1>
    <p style="color: #7eb3ff; margin:0;">
        Ask me anything about Admissions, Placements or Career Guidance
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# CHAT HISTORY DISPLAY
# ─────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #4a5568;">
            <h2>👋 Welcome to CIT Assistant!</h2>
            <p>I can help you with:</p>
            <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; margin-top:20px;">
                <div style="background:#1a1a2e; padding:15px 25px; border-radius:12px;
                            border:1px solid #4cff91; color:#4cff91;">
                    🎓 Admissions & Eligibility
                </div>
                <div style="background:#1a1a2e; padding:15px 25px; border-radius:12px;
                            border:1px solid #ffb74d; color:#ffb74d;">
                    💼 Placements & Companies
                </div>
                <div style="background:#1a1a2e; padding:15px 25px; border-radius:12px;
                            border:1px solid #ce93d8; color:#ce93d8;">
                    🚀 Career Guidance
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f"<div class='user-message'>👤 {msg['content']}</div>",
                unsafe_allow_html=True
            )
        else:
            agent_key  = msg.get("agent", "admissions")
            info       = AGENT_INFO[agent_key]
            sources    = msg.get("sources", [])

            source_tags = " ".join([
                f"<span class='source-tag'>📎 {s}</span>"
                for s in sources
            ])

            st.markdown(f"""
            <div class='bot-message'>
                <div>
                    <span class='agent-badge {info["badge"]}'>{info["label"]}</span>
                </div>
                {msg["content"]}
                <div style="margin-top:10px;">
                    {source_tags}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# FOLLOW-UP QUESTIONS
# ─────────────────────────────────────────
if st.session_state.followup_questions:
    st.markdown(
        "<p style='color:#7eb3ff; font-size:13px; margin-top:15px;'>"
        "💡 You might also want to ask:</p>",
        unsafe_allow_html=True
    )
    cols = st.columns(3)
    for i, question in enumerate(st.session_state.followup_questions):
        with cols[i]:
            if st.button(f"➤ {question}", key=f"followup_{i}"):
                st.session_state.pending_question = question
                st.rerun()


# ─────────────────────────────────────────
# PROCESS QUESTION (from input or buttons)
# ─────────────────────────────────────────
def process_question(user_input: str):
    st.session_state.chat_history.append({
        "role"   : "user",
        "content": user_input
    })

    route_result = route(user_input)
    agent_name   = route_result["agent"]
    confidence   = route_result["confidence"]
    info         = AGENT_INFO[agent_name]
    badge        = info["badge"]
    label        = info["label"]

    st.markdown(
        f"<div style='color:#7eb3ff; font-size:12px; margin:4px 0;'>"
        f"🔀 Routing to {label} (confidence: {confidence})"
        f"</div>",
        unsafe_allow_html=True
    )

    sources_captured = []
    full_response    = ""

    # ← Key fix: assign directly, no "with"
    stream_box = st.empty()

    for token, sources in agents[agent_name].answer_stream(
        user_input,
        chat_history=st.session_state.chat_history
    ):
        full_response    += token
        sources_captured  = sources

        stream_box.markdown(
            f"<div class='bot-message'>"
            f"<span class='agent-badge {badge}'>{label}</span>"
            f"<div style='margin-top:8px;'>{full_response}▌</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Final render without cursor
    source_tags = " ".join([
        f"<span class='source-tag'>📎 {s}</span>"
        for s in sources_captured
    ])

    stream_box.markdown(
        f"<div class='bot-message'>"
        f"<span class='agent-badge {badge}'>{label}</span>"
        f"<div style='margin-top:8px;'>{full_response}</div>"
        f"<div style='margin-top:10px;'>{source_tags}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.session_state.chat_history.append({
        "role"   : "assistant",
        "content": full_response,
        "agent"  : agent_name,
        "sources": sources_captured
    })

    st.session_state.total_questions += 1
    st.session_state.agent_counts[agent_name] += 1

    followups = agents[agent_name].suggest_followups(user_input)
    st.session_state.followup_questions = followups

    st.rerun()

# ─────────────────────────────────────────
# Handle pending question (from buttons)
# ─────────────────────────────────────────
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    process_question(question)


# ─────────────────────────────────────────
# CHAT INPUT
# ─────────────────────────────────────────
user_input = st.chat_input(
    "Ask about admissions, placements or career guidance..."
)

if user_input:
    process_question(user_input)