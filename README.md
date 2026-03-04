# 🎓 CIT Smart Assistant — Multi-Agent RAG Chatbot

A production-ready AI chatbot for **Chennai Institute of Technology (CIT)** that answers student queries about Admissions, Placements, and Career Guidance using Retrieval-Augmented Generation (RAG) with multiple specialized agents.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#%EF%B8%8F-tech-stack)
- [Project Structure](#-project-structure)
- [Setup and Installation](#%EF%B8%8F-setup-and-installation)
- [How to Run](#-how-to-run)
- [How It Works](#%EF%B8%8F-how-it-works)
- [Agents](#-agents)
- [Knowledge Base](#-knowledge-base)

---

## 🧠 Overview

CIT Smart Assistant is a multi-agent AI chatbot that helps students get instant, accurate answers about:
- College admissions, cutoffs, eligibility, and courses
- Placement statistics, recruiting companies, and training
- Career paths, higher studies, skills, and industry trends

Instead of one large general-purpose model, the system uses **three specialized agents**, each with its own knowledge base, routed intelligently using a lightweight semantic router.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 Multi-Agent System | 3 specialized agents for Admissions, Placements, Career Guidance |
| 🔀 Semantic Router | Lightweight local model routes queries with zero API calls |
| 📚 RAG Pipeline | Retrieves relevant chunks from ChromaDB before answering |
| ⚡ Streaming Responses | Tokens appear word-by-word like ChatGPT |
| 💾 Persistent Vector DB | ChromaDB built once, loaded instantly on every run |
| 📎 Source Attribution | Shows which document the answer came from |
| 💡 Follow-up Suggestions | Agent suggests 3 related questions after every answer |
| 📊 Session Stats | Live tracking of questions asked per agent |
| 🌙 Dark Theme UI | Clean professional Streamlit interface |
| 🕐 Chat History | Remembers last 4 messages for context-aware answers |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│     (Dark UI + Streaming + Stats + Follow-ups)       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         Semantic Router (all-MiniLM-L6-v2)          │
│    Classifies query using cosine similarity         │
│         No API call — runs 100% locally             │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
           ▼              ▼              ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  Admissions  │ │  Placements  │ │   Career     │
   │    Agent     │ │    Agent     │ │  Guidance    │
   │              │ │              │ │   Agent      │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────────────────────────────────────────┐
   │           ChromaDB Vector Store              │
   │   BAAI/bge-small-en-v1.5 Embeddings (local) │
   │         Persistent — built only once         │
   └──────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────────────────────────────────────────┐
   │         NVIDIA NIM API — GPT-OSS-20B         │
   │     Generates answer from retrieved context  │
   └──────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | NVIDIA NIM API — `openai/gpt-oss-20b` |
| Embeddings | `BAAI/bge-small-en-v1.5` (local, 133MB) |
| Router Model | `all-MiniLM-L6-v2` (local, 80MB) |
| Vector Database | ChromaDB (persistent) |
| RAG Framework | LangChain |
| Frontend | Streamlit |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
chatbot-for-college/
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Core RAG logic, ChromaDB, streaming
│   ├── admissions_agent.py    # Admissions specialist
│   ├── placements_agent.py    # Placements specialist
│   └── career_agent.py        # Career guidance specialist
│
├── data/
│   ├── admissions_knowledge.json     # Cutoffs, eligibility, courses
│   ├── placements_knowledge.json     # Stats, companies, training
│   └── career_guidance_knowledge.json # Career paths, skills, trends
│
├── chromadb/                  # Auto-created on first run
│   ├── admissions/
│   ├── placements/
│   └── career_guidance/
│
├── agent_router.py            # Semantic routing logic
├── app.py                     # Streamlit web application
├── test.py                    # Pipeline testing script
├── convert_to_json.py         # Data preparation script
├── requirements.txt
├── .env                       # API keys (not committed)
└── README.md
```

---

## ⚙️ Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Naveen300305/chatbot-for-college.git
cd chatbot-for-college
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

Create a `.env` file in the project root:
```
NVIDIA_API_KEY=your_nvidia_api_key_here
```

> 💡 Get your free NVIDIA API key at [build.nvidia.com](https://build.nvidia.com)

### 5. Add Knowledge Base Files

Place your JSON knowledge files in the `data/` folder:
```
data/admissions_knowledge.json
data/placements_knowledge.json
data/career_guidance_knowledge.json
```

---

## 🚀 How to Run

### Run the Web App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`

### Run the Test Pipeline
```bash
python test.py
```

### Test the Router Only
```bash
python agent_router.py
```

---

## ⚙️ How It Works

### Step 1: Data Preparation
- College data (TXT, CSV) converted to structured JSON
- JSON split into chunks using `RecursiveCharacterTextSplitter`
- Chunks embedded using `BAAI/bge-small-en-v1.5` and stored in ChromaDB

### Step 2: Routing
- User message encoded using `all-MiniLM-L6-v2`
- Cosine similarity computed against 3 agent description vectors
- Query routed to the agent with highest similarity score
- Entire routing runs locally — zero API call — near-zero latency

### Step 3: RAG
- Routed agent queries ChromaDB for top 4 relevant chunks
- Chunks assembled into context with source metadata
- Context + question sent to NVIDIA NIM API (GPT-OSS-20B)
- Response streamed back token by token

### Step 4: Display
- Tokens appear word by word in Streamlit UI
- Sources shown as tags below the answer
- Follow-up questions suggested automatically
- Chat history maintained for context-aware conversations

---

## 🤖 Agents

### 🎓 Admissions Agent
Handles questions about:
- Branch-wise cutoff marks (TNEA 2025)
- Eligibility criteria (B.E., B.Tech, M.E.)
- Lateral entry, NRI, OCI, Foreign National admissions
- SAT score admissions
- Courses offered, syllabus, regulations
- Centers of Excellence

### 💼 Placements Agent
Handles questions about:
- Placement statistics (2023-24, 2024-25, 2025-26)
- Recruiting companies (Amazon, Microsoft, Zoho, etc.)
- Salary packages and LPA ranges
- Internship programs
- Training methods and CDC activities
- Foreign language training

### 🚀 Career Guidance Agent
Handles questions about:
- Career paths after each course
- Top recruiting companies by branch
- Skills required for each career
- Higher studies options (GATE, MS abroad, MBA)
- Industry trends and salary insights
- Chennai as a tech hub

---

## 📊 Knowledge Base

### Data Sources
All data collected from Chennai Institute of Technology official website and structured into JSON format.

### Data Format
Each agent's knowledge base follows this structure:
```json
{
  "agent": "admissions",
  "text_data": [
    {"topic": "topic name", "content": "text content"}
  ],
  "table_data": [
    {"topic": "topic name", "data": [{"col1": "val1"}]}
  ],
  "structured_data": [
    {"topic": "topic name", "data": {...}}
  ]
}
```

### Embedding Model
- Model: `BAAI/bge-small-en-v1.5`
- Size: 133MB
- Runs fully locally
- Normalized embeddings for accurate cosine similarity

---


## 🔑 Key Technical Decisions

| Decision | Reason |
|----------|--------|
| Local router model | Zero API calls = near-zero routing latency |
| Persistent ChromaDB | Vector DB built once, loads instantly every run |
| BAAI/bge-small-en-v1.5 | Small, fast, accurate embeddings — runs locally |
| Streaming responses | Perceived latency near zero — tokens appear instantly |
| Separate agents per domain | Better accuracy — each agent focused on one topic |
| GPT-OSS-20B via NVIDIA NIM | Free credits, fast inference, strong instruction following |

---

## 📦 Requirements

```
langchain
langchain-core
langchain-community
langchain-text-splitters
langchain-nvidia-ai-endpoints
chromadb
sentence-transformers
streamlit
python-dotenv
torch
transformers
```

---

## 👤 Author

**Naveen** — Chennai Institute of Technology
- Project: AI Agents for College Enquiry System
- Stack: Python · LangChain · ChromaDB · NVIDIA NIM · Streamlit

---

## 📝 License

This project is built for academic purposes at Chennai Institute of Technology.
