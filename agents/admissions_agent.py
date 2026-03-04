from agents.base_agent import BaseAgent


class AdmissionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="admissions",
            json_path="output/admissions_knowledge.json"
        )