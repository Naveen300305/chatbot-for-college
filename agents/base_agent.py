import json
import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction

load_dotenv()

# ─────────────────────────────────────────
# Custom Embedding Function using
# BAAI/bge-small-en-v1.5 (local model)
# ─────────────────────────────────────────
class BGEEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        print("  [🔧] Loading BAAI/bge-small-en-v1.5 embedding model...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("  [✅] Embedding model loaded!")

    def __call__(self, input):
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


# Load embedding model once — shared across all agents
embedding_function = BGEEmbeddingFunction()


class BaseAgent:
    def __init__(self, agent_name: str, json_path: str):
        self.agent_name = agent_name
        self.persist_dir = f"./chromadb/{agent_name}"
        self.api_key = os.getenv("NVIDIA_API_KEY")

        print(f"\n  [🔧] Initializing {agent_name} agent...")

        # NVIDIA LLM
        self.llm = ChatNVIDIA(
            model="openai/gpt-oss-20b",
            nvidia_api_key=self.api_key,
            temperature=0.3,
            max_tokens=1024
        )

        # ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_dir
        )

        # Load existing or build new collection
        existing = [c.name for c in self.chroma_client.list_collections()]

        if agent_name in existing:
            print(f"  [✅] Loading existing ChromaDB for {agent_name}...")
            self.collection = self.chroma_client.get_collection(
                name=agent_name,
                embedding_function=embedding_function
            )
        else:
            print(f"  [🔨] Building ChromaDB for {agent_name}...")
            self.collection = self._build_vectorstore(json_path)
            print(f"  [✅] ChromaDB built and saved for {agent_name}!")

    # ─────────────────────────────────────────
    # Build vector store from JSON
    # ─────────────────────────────────────────
    def _build_vectorstore(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        metadatas = []
        ids = []
        counter = 0

        # 1. Text data
        for item in data.get("text_data", []):
            documents.append(item["content"])
            metadatas.append({
                "topic": item["topic"],
                "type": "text"
            })
            ids.append(f"{self.agent_name}_text_{counter}")
            counter += 1

        # 2. Table data
        for item in data.get("table_data", []):
            table_text = f"Topic: {item['topic']}\n"
            for row in item["data"]:
                table_text += " | ".join(
                    f"{k}: {v}" for k, v in row.items() if v
                ) + "\n"
            documents.append(table_text)
            metadatas.append({
                "topic": item["topic"],
                "type": "table"
            })
            ids.append(f"{self.agent_name}_table_{counter}")
            counter += 1

        # 3. Structured data
        for item in data.get("structured_data", []):
            structured_text = f"Topic: {item['topic']}\n"
            structured_text += json.dumps(item["data"], indent=2)
            documents.append(structured_text)
            metadatas.append({
                "topic": item["topic"],
                "type": "structured"
            })
            ids.append(f"{self.agent_name}_structured_{counter}")
            counter += 1

        # Split long documents into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )

        final_docs = []
        final_metas = []
        final_ids = []
        chunk_counter = 0

        for doc, meta, doc_id in zip(documents, metadatas, ids):
            chunks = splitter.split_text(doc)
            for i, chunk in enumerate(chunks):
                final_docs.append(chunk)
                final_metas.append(meta)
                final_ids.append(f"{doc_id}_chunk_{i}_{chunk_counter}")
                chunk_counter += 1

        print(f"  [📄] Created {len(final_docs)} chunks for {self.agent_name}")

        # Create collection and add documents
        collection = self.chroma_client.create_collection(
            name=self.agent_name,
            embedding_function=embedding_function
        )

        # Add in batches of 100
        batch_size = 100
        for i in range(0, len(final_docs), batch_size):
            collection.add(
                documents=final_docs[i:i+batch_size],
                metadatas=final_metas[i:i+batch_size],
                ids=final_ids[i:i+batch_size]
            )

        return collection

    # ─────────────────────────────────────────
    # Answer using RAG
    # ─────────────────────────────────────────
    def answer(self, user_question: str, chat_history: list = []) -> dict:
        # Retrieve top 4 relevant chunks
        results = self.collection.query(
            query_texts=[user_question],
            n_results=4
        )

        # Build context from retrieved chunks
        chunks = results["documents"][0]
        metas = results["metadatas"][0]

        context = "\n\n---\n\n".join([
            f"[Source: {meta.get('topic', 'unknown')}]\n{chunk}"
            for chunk, meta in zip(chunks, metas)
        ])

        sources = list(set([
            meta.get("topic", "unknown") for meta in metas
        ]))

        # Build chat history (last 4 messages)
        history_text = ""
        if chat_history:
            for msg in chat_history[-4:]:
                role = "Student" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"

        prompt = f"""You are a helpful assistant for Chennai Institute of Technology (CIT).
You MUST answer using the context below. The context contains real data from CIT.

IMPORTANT RULES:
- You MUST use the information from the context to answer
- If numbers, statistics or lists are in the context — USE THEM in your answer
- Only say "I don't have that information" if the context has ZERO relevant info
- Be friendly, clear and use bullet points for lists
- Always refer to the college as CIT or Chennai Institute of Technology

{f"Previous conversation:{chr(10)}{history_text}" if history_text else ""}

Context from CIT knowledge base:
{context}

Student Question: {user_question}

Answer (use the context data above):"""

        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "sources": sources,
            "agent": self.agent_name
        }



    def answer_stream(self, user_question: str, chat_history: list = []):
        """Same as answer() but streams tokens one by one"""

        # Retrieve top 4 relevant chunks
        results = self.collection.query(
            query_texts=[user_question],
            n_results=4
        )

        chunks = results["documents"][0]
        metas  = results["metadatas"][0]

        context = "\n\n---\n\n".join([
            f"[Source: {meta.get('topic', 'unknown')}]\n{chunk}"
            for chunk, meta in zip(chunks, metas)
        ])

        sources = list(set([
            meta.get("topic", "unknown") for meta in metas
        ]))

        # Build chat history
        history_text = ""
        if chat_history:
            for msg in chat_history[-4:]:
                role = "Student" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"

        prompt = f"""You are a helpful assistant for Chennai Institute of Technology (CIT).
    You MUST answer using the context below. The context contains real data from CIT.

    IMPORTANT RULES:
    - You MUST use the information from the context to answer
    - If numbers, statistics or lists are in the context — USE THEM in your answer
    - Only say "I don't have that information" if the context has ZERO relevant info
    - Be friendly, clear and use bullet points for lists
    - Always refer to the college as CIT or Chennai Institute of Technology

    {f"Previous conversation:{chr(10)}{history_text}" if history_text else ""}

    Context from CIT knowledge base:
    {context}

    Student Question: {user_question}

    Answer (use the context data above):"""

        # Stream tokens one by one
        for chunk in self.llm.stream(prompt):
            yield chunk.content, sources

    # ─────────────────────────────────────────
    # Suggest follow-up questions
    # ─────────────────────────────────────────
    def suggest_followups(self, user_question: str) -> list:
        prompt = f"""Based on this student question about Chennai Institute of Technology:
"{user_question}"

Generate exactly 3 short follow-up questions a student might ask next.
Return ONLY the 3 questions, one per line, no numbering, no extra text."""

        response = self.llm.invoke(prompt)
        questions = [
            q.strip() for q in response.content.strip().split("\n")
            if q.strip()
        ]
        return questions[:3]

