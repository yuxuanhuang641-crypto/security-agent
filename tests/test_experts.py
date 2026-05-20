import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents import build_exploit_expert, build_recon_expert  # noqa: E402
from agents.json_utils import ExpertOutputError, validate_expert_output  # noqa: E402


class ExpertNodeTests(unittest.TestCase):
    def test_recon_mock_generates_nmap_command(self):
        node = build_recon_expert()
        state = {"recon_messages": [{"role": "user", "content": "扫描 127.0.0.1 的 1100 端口"}]}

        new_state = node(state)

        self.assertEqual(new_state["pending_tool"], "nmap")
        self.assertEqual(new_state["pending_command"], "nmap -sV -Pn -p 1100 127.0.0.1")
        self.assertEqual(new_state["recon_output"]["status"], "ready")

    def test_exploit_mock_generates_low_risk_sqlmap_command(self):
        node = build_exploit_expert()
        state = {
            "exploit_messages": [
                {
                    "role": "user",
                    "content": "对 http://127.0.0.1:8080/item?id=1 做授权 SQL 注入检测",
                }
            ]
        }

        new_state = node(state)

        self.assertEqual(new_state["pending_tool"], "sqlmap")
        self.assertIn("--level 1", new_state["pending_command"])
        self.assertIn("--risk 1", new_state["pending_command"])

    def test_exploit_skeleton_requires_url(self):
        node = build_exploit_expert()
        state = {"exploit_messages": [{"role": "user", "content": "尝试利用目标漏洞"}]}

        new_state = node(state)

        self.assertNotIn("pending_command", new_state)
        self.assertEqual(new_state["exploit_output"]["status"], "need_more_info")

    def test_rejects_shell_chaining(self):
        with self.assertRaises(ExpertOutputError):
            validate_expert_output(
                {
                    "tool": "nmap",
                    "command": "nmap -sV -p 80 127.0.0.1; rm -rf /",
                    "status": "ready",
                },
                expected_tool="nmap",
            )

    def test_custom_llm_json_fence_is_parsed(self):
        def fake_llm(*, system_prompt, user_prompt, state):
            del system_prompt, user_prompt, state
            return "```json\n" + json.dumps(
                {
                    "tool": "nmap",
                    "command": "nmap -sV -Pn -p 80 127.0.0.1",
                    "status": "ready",
                }
            ) + "\n```"

        node = build_recon_expert(llm_call=fake_llm)
        new_state = node({"recon_messages": [{"role": "user", "content": "scan local port 80"}]})

        self.assertEqual(new_state["pending_command"], "nmap -sV -Pn -p 80 127.0.0.1")


if __name__ == "__main__":
    unittest.main()
