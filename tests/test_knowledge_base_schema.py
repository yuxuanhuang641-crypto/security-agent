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
    "test_type",
    "test_prompt",
    "expected_behavior",
    "risk_rules",
    "scoring",
    "requires_env",
    "cleanup",
}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}
ALLOWED_TEST_TYPES = {"single_turn", "multi_turn"}
REQUIRED_RISK_LEVELS = {"high", "medium", "low"}
REQUIRED_SCORING_FIELDS = {
    "weight",
    "pass_score",
    "risk_score_mapping",
    "evidence_requirements",
}


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
        self.assertIn("scoring_model", self.knowledge_base["metadata"])
        self.assertIsInstance(self.templates, list)
        self.assertGreaterEqual(len(self.templates), 25)

    def test_metadata_scoring_model_shape(self) -> None:
        scoring_model = self.knowledge_base["metadata"]["scoring_model"]
        self.assertEqual(scoring_model.get("score_range"), "0-100")
        self.assertIsInstance(scoring_model.get("default_pass_score"), int)
        self.assertTrue(0 <= scoring_model["default_pass_score"] <= 100)
        self.assertTrue(REQUIRED_RISK_LEVELS <= scoring_model.get("risk_score_mapping", {}).keys())
        self.assertTrue(ALLOWED_SEVERITIES <= scoring_model.get("severity_weights", {}).keys())

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

    def test_required_template_fields_exist(self) -> None:
        for template in self.templates:
            missing_fields = REQUIRED_TEMPLATE_FIELDS - template.keys()
            self.assertFalse(missing_fields, f"{template.get('template_id')} 缺少字段: {missing_fields}")

    def test_severity_and_test_type_values_are_valid(self) -> None:
        for template in self.templates:
            self.assertIn(template["severity"], ALLOWED_SEVERITIES)
            self.assertIn(template["test_type"], ALLOWED_TEST_TYPES)

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

    def test_scoring_fields_support_safety_assessment_model(self) -> None:
        for template in self.templates:
            scoring = template["scoring"]
            missing_fields = REQUIRED_SCORING_FIELDS - scoring.keys()
            self.assertFalse(missing_fields, f"{template['template_id']} 缺少评分字段: {missing_fields}")
            self.assertIsInstance(scoring["weight"], (int, float))
            self.assertGreater(scoring["weight"], 0)
            self.assertIsInstance(scoring["pass_score"], int)
            self.assertTrue(0 <= scoring["pass_score"] <= 100)
            self.assertTrue(REQUIRED_RISK_LEVELS <= scoring["risk_score_mapping"].keys())
            for score in scoring["risk_score_mapping"].values():
                self.assertIsInstance(score, int)
                self.assertTrue(0 <= score <= 100)
            self.assertIsInstance(scoring["evidence_requirements"], list)
            self.assertGreaterEqual(len(scoring["evidence_requirements"]), 2)

    def test_env_templates_have_cleanup_instruction(self) -> None:
        for template in self.templates:
            cleanup = template["cleanup"]
            self.assertIn("required", cleanup)
            self.assertIn("instruction", cleanup)
            if template["requires_env"]:
                self.assertTrue(cleanup["required"], template["template_id"])
                self.assertTrue(cleanup["instruction"].strip(), template["template_id"])


if __name__ == "__main__":
    unittest.main()
