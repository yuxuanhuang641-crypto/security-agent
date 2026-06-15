"""校验 AI 安全审计知识库的结构完整性。"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE_PATH = REPO_ROOT / "knowledge_base" / "ai_safety_knowledge_base.json"

REQUIRED_TEMPLATE_FIELDS = {
    "template_id",
    "name",
    "category",
    "severity",
    "score",
    "attack_category",
    "endpoint_type",
    "owasp_mapping",
    "atlas_mapping",
    "priority_tags",
    "test_type",
    "test_prompt",
    "expected_behavior",
    "risk_rules",
    "requires_env",
    "cleanup",
}
FORBIDDEN_TEMPLATE_FIELDS = {"scoring", "risk_level", "status"}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}
ALLOWED_TEST_TYPES = {"single_turn", "multi_turn"}
ALLOWED_PRIORITY_LEVELS = {"P0", "P1", "P2", "P3"}
REQUIRED_RISK_LEVELS = {"high", "medium", "low"}


class KnowledgeBaseSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with KNOWLEDGE_BASE_PATH.open("r", encoding="utf-8") as file:
            cls.knowledge_base: dict[str, Any] = json.load(file)
        cls.templates: list[dict[str, Any]] = cls.knowledge_base.get("templates", [])

    def test_json_has_top_level_sections(self) -> None:
        self.assertIn("metadata", self.knowledge_base)
        self.assertIn("templates", self.knowledge_base)
        self.assertIsInstance(self.knowledge_base["metadata"], dict)
        self.assertIn("score_model", self.knowledge_base["metadata"])
        self.assertNotIn("scoring_model", self.knowledge_base["metadata"])
        self.assertIsInstance(self.templates, list)
        self.assertGreaterEqual(len(self.templates), 28)

    def test_metadata_score_model_shape(self) -> None:
        score_model = self.knowledge_base["metadata"]["score_model"]
        self.assertEqual(score_model.get("score_range"), "0-4")
        self.assertIsInstance(score_model.get("score_meaning"), str)
        self.assertTrue(score_model["score_meaning"].strip())
        levels = score_model.get("levels", {})
        self.assertEqual(set(levels.keys()), {"0", "1", "2", "3", "4"})
        for description in levels.values():
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())
        self.assertIsInstance(score_model.get("aggregation_note"), str)

    def test_template_count_matches_metadata(self) -> None:
        metadata_count = self.knowledge_base["metadata"].get("template_count")
        self.assertEqual(metadata_count, len(self.templates))

    def test_no_placeholder_garbled_text(self) -> None:
        raw_text = json.dumps(self.knowledge_base, ensure_ascii=False)
        self.assertNotIn("???", raw_text)

    def test_template_ids_are_unique_and_snake_case(self) -> None:
        template_ids = [template.get("template_id") for template in self.templates]
        self.assertEqual(len(template_ids), len(set(template_ids)))
        for template_id in template_ids:
            self.assertIsInstance(template_id, str)
            self.assertRegex(template_id, r"^[a-z][a-z0-9_]*$")

    def test_required_template_fields_exist_and_old_static_fields_removed(self) -> None:
        for template in self.templates:
            missing_fields = REQUIRED_TEMPLATE_FIELDS - template.keys()
            self.assertFalse(missing_fields, f"{template.get('template_id')} 缺少字段: {missing_fields}")
            forbidden_fields = FORBIDDEN_TEMPLATE_FIELDS & template.keys()
            self.assertFalse(forbidden_fields, f"{template.get('template_id')} 仍包含旧字段: {forbidden_fields}")

    def test_severity_and_test_type_values_are_valid(self) -> None:
        for template in self.templates:
            self.assertIn(template["severity"], ALLOWED_SEVERITIES)
            self.assertIn(template["test_type"], ALLOWED_TEST_TYPES)

    def test_score_and_coverage_fields_are_valid(self) -> None:
        for template in self.templates:
            self.assertIs(type(template["score"]), int, template["template_id"])
            self.assertTrue(0 <= template["score"] <= 4, template["template_id"])
            self.assertIsInstance(template["attack_category"], str)
            self.assertTrue(template["attack_category"].strip(), template["template_id"])
            self.assertIsInstance(template["endpoint_type"], str)
            self.assertTrue(template["endpoint_type"].startswith("/"), template["template_id"])

            for field in ("owasp_mapping", "atlas_mapping", "priority_tags"):
                self.assertIsInstance(template[field], list, template["template_id"])
                self.assertGreaterEqual(len(template[field]), 1, template["template_id"])
                for item in template[field]:
                    self.assertIsInstance(item, str)
                    self.assertTrue(item.strip(), template["template_id"])

            priority_levels = set(template["priority_tags"]) & ALLOWED_PRIORITY_LEVELS
            self.assertTrue(priority_levels, template["template_id"])

    def test_test_prompt_shape_matches_test_type(self) -> None:
        for template in self.templates:
            if template["test_type"] == "multi_turn":
                self.assertIsInstance(template["test_prompt"], list)
                for item in template["test_prompt"]:
                    self.assertIn("round", item)
                    self.assertIn("content", item)
            else:
                self.assertIsInstance(template["test_prompt"], str)
                self.assertTrue(template["test_prompt"].strip())

    def test_risk_rules_have_required_levels_and_shape(self) -> None:
        for template in self.templates:
            risk_rules = template["risk_rules"]
            self.assertTrue(REQUIRED_RISK_LEVELS <= risk_rules.keys())
            for level in REQUIRED_RISK_LEVELS:
                rule = risk_rules[level]
                self.assertIsInstance(rule.get("keywords"), list)
                self.assertIsInstance(rule.get("patterns"), list)
                self.assertIsInstance(rule.get("description"), str)
                self.assertTrue(rule["description"].strip())
                for pattern in rule["patterns"]:
                    re.compile(pattern)

    def test_env_templates_have_cleanup_instruction(self) -> None:
        for template in self.templates:
            cleanup = template["cleanup"]
            self.assertIn("required", cleanup)
            self.assertIn("instruction", cleanup)
            if template["requires_env"]:
                self.assertTrue(cleanup["required"], template["template_id"])
                self.assertTrue(cleanup["instruction"].strip(), template["template_id"])

    def test_openclaw_special_templates_exist(self) -> None:
        openclaw_templates = [
            template
            for template in self.templates
            if template["template_id"].startswith("openclaw_")
        ]
        self.assertGreaterEqual(len(openclaw_templates), 3)
        for template in openclaw_templates:
            self.assertTrue(template["requires_env"], template["template_id"])
            self.assertIn("OpenClaw", template["priority_tags"], template["template_id"])


if __name__ == "__main__":
    unittest.main()
