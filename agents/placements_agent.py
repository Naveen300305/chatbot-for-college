from agents.base_agent import BaseAgent


class PlacementsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="placements",
            json_path="output/placements_knowledge.json"
        )