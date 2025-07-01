import unittest

from src.crew_assistant.agents.commander import commander
from src.crew_assistant.agents.dev import dev
from src.crew_assistant.agents.planner import planner


class TestAgents(unittest.TestCase):
    def test_planner_exists(self):
        self.assertIsNotNone(planner)

    def test_dev_exists(self):
        self.assertIsNotNone(dev)

    def test_commander_exists(self):
        self.assertIsNotNone(commander)


if __name__ == "__main__":
    unittest.main()
