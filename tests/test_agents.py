import unittest

from crew_assistant.agents.commander import CommanderAgent
from crew_assistant.agents.dev import DeveloperAgent
from crew_assistant.agents.planner import PlannerAgent
from crew_assistant.agents.ux import UXAgent
from crew_assistant.agents.reviewer import ReviewerAgent


class TestAgents(unittest.TestCase):
    def test_planner_agent_exists(self):
        self.assertIsNotNone(PlannerAgent)

    def test_developer_agent_exists(self):
        self.assertIsNotNone(DeveloperAgent)

    def test_commander_agent_exists(self):
        self.assertIsNotNone(CommanderAgent)
        
    def test_ux_agent_exists(self):
        self.assertIsNotNone(UXAgent)
        
    def test_reviewer_agent_exists(self):
        self.assertIsNotNone(ReviewerAgent)


if __name__ == "__main__":
    unittest.main()