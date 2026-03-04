from agents.base_agent import BaseAgent


class CareerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="career_guidance",
            json_path="output/Carrer_guidance.json"
        )