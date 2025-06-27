import unittest
from agents.planner import planner
from agents.dev import dev
from agents.commander import commander

class TestAgents(unittest.TestCase):

    def test_planner_exists(self):
        self.assertIsNotNone(planner)

    def test_dev_exists(self):
        self.assertIsNotNone(dev)

    def test_commander_exists(self):
        self.assertIsNotNone(commander)

if __name__ == '__main__':
    unittest.main()
