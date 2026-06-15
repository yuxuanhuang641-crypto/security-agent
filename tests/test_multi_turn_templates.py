"""专门校验多轮对话检测模板。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_PATH = REPO_ROOT / "knowledge_base" / "ai_safety_knowledge_base.json"
ALLOWED_SESSION_STRATEGIES = {
    "same_session",
    "cross_session_same_user",
    "cross_session_different_user",
}


class MultiTurnTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as file:
            knowledge_base: dict[str, Any] = json.load(file)
        cls.multi_turn_templates = [
            template
            for template in knowledge_base["templates"]
            if template["test_type"] == "multi_turn"
        ]

    def test_has_enough_multi_turn_templates(self) -> None:
        self.assertGreaterEqual(len(self.multi_turn_templates), 7)

    def test_rounds_are_ordered_and_non_empty(self) -> None:
        for template in self.multi_turn_templates:
            rounds = template["test_prompt"]
            self.assertEqual([item["round"] for item in rounds], list(range(1, len(rounds) + 1)))
            for item in rounds:
                self.assertTrue(item["content"].strip(), template["template_id"])

    def test_multi_turn_config_is_complete(self) -> None:
        for template in self.multi_turn_templates:
            self.assertIn("multi_turn_config", template, template["template_id"])
            config = template["multi_turn_config"]
            self.assertIn(config["session_strategy"], ALLOWED_SESSION_STRATEGIES)
            self.assertEqual(config["turn_count"], len(template["test_prompt"]), template["template_id"])
            self.assertIsInstance(config["state_assertions"], list)
            self.assertGreaterEqual(len(config["state_assertions"]), 1, template["template_id"])
            for assertion in config["state_assertions"]:
                self.assertIsInstance(assertion, str)
                self.assertTrue(assertion.strip(), template["template_id"])
            self.assertIsInstance(config["success_criteria"], str)
            self.assertTrue(config["success_criteria"].strip(), template["template_id"])

    def test_cross_session_templates_reset_between_rounds(self) -> None:
        for template in self.multi_turn_templates:
            config = template["multi_turn_config"]
            if config["session_strategy"].startswith("cross_session"):
                self.assertTrue(config["reset_between_rounds"], template["template_id"])

    def test_multi_turn_templates_use_new_score_model(self) -> None:
        for template in self.multi_turn_templates:
            self.assertIn("score", template, template["template_id"])
            self.assertNotIn("scoring", template, template["template_id"])
            self.assertTrue(0 <= template["score"] <= 4, template["template_id"])


if __name__ == "__main__":
    unittest.main()
