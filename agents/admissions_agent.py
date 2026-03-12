from agents.base_agent import BaseAgent


# Keywords that mean user wants a simple list of courses (not syllabus detail)
_LIST_KEYWORDS = [
    'list', 'all courses', 'courses offered', 'what courses', 'which courses',
    'available courses', 'programs offered', 'programmes offered',
    'what programmes', 'what programs', 'what branches', 'all branches',
    'what can i study', 'what do you offer', 'courses available'
]

# Keywords that indicate the user is asking about courses/programmes (broad)
_COURSE_KEYWORDS = [
    'course', 'courses', 'program', 'programme', 'programs', 'programmes',
    'branch', 'branches', 'department', 'departments', 'offered', 'offer',
    'degree', 'degrees', 'b.e', 'b.tech', 'm.e', 'ug', 'pg',
    'undergraduate', 'postgraduate', 'what can i study', 'what do you offer',
    'available courses', 'all courses', 'list course'
]

# Topics to EXCLUDE from semantic results when the user just wants a listing
# (the syllabus JSON causes the LLM to over-explain every course)
_LISTING_EXCLUDE_TOPICS = {'All Course Syllabus'}


class AdmissionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="admissions",
            json_path="output/admissions_knowledge.json"
        )

    def _is_listing_query(self, question: str) -> bool:
        q = question.lower()
        return any(kw in q for kw in _LIST_KEYWORDS)

    def _get_mandatory_chunks(self, user_question: str) -> tuple:
        """Always include 'courses offered' doc when the query is about courses."""
        query_lower = user_question.lower()
        if not any(kw in query_lower for kw in _COURSE_KEYWORDS):
            return [], []
        try:
            result = self.collection.get(
                where={"topic": "courses offered"},
                include=["documents", "metadatas"]
            )
            docs = result.get("documents") or []
            metas = result.get("metadatas") or []
            return docs, metas
        except Exception:
            return [], []

    def _merge_chunks(self, mandatory_docs, mandatory_metas, sem_docs, sem_metas, user_question=""):
        """For simple listing queries, strip out heavy syllabus chunks so the LLM
        doesn't describe every course in detail. For syllabus detail queries,
        keep All Course Syllabus in context so the LLM can answer properly."""
        if mandatory_docs and self._is_listing_query(user_question):
            filtered_docs = []
            filtered_metas = []
            for doc, meta in zip(sem_docs, sem_metas):
                if meta.get("topic") not in _LISTING_EXCLUDE_TOPICS:
                    filtered_docs.append(doc)
                    filtered_metas.append(meta)
            sem_docs, sem_metas = filtered_docs, filtered_metas

        return super()._merge_chunks(
            mandatory_docs, mandatory_metas, sem_docs, sem_metas, user_question
        )