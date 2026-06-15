# Knowledge Base Coverage Matrix

This document summarizes framework mapping, target endpoint, impact score, priority, and environment requirements for every AI safety audit template.

- OWASP mapping follows OWASP Top 10 for LLM Applications 2025 naming.
- ATLAS mapping uses MITRE ATLAS direction names; technique IDs are not mandatory in this phase.
- `score` is the theoretical maximum impact if the template is successfully exploited. It does not mean the current system has already been compromised.

| template_id | category | attack_category | score | owasp_mapping | atlas_mapping | endpoint_type | priority_tags | requires_env |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `prompt_injection_basic` | 用户输入安全 | Prompt Injection | 3 | LLM01:2025 Prompt Injection<br>LLM07:2025 System Prompt Leakage | Prompt Injection<br>System Prompt Discovery | `/v1/chat/completions` | P1 | false |
| `encoding_bypass_injection` | 用户输入安全 | Prompt Injection | 2 | LLM01:2025 Prompt Injection | Prompt Injection<br>Obfuscated Prompt | `/v1/chat/completions` | P2 | false |
| `rag_poisoning_basic` | 检索内容进入安全 | Data Poisoning | 3 | LLM04:2025 Data and Model Poisoning<br>LLM08:2025 Vector and Embedding Weaknesses | Data Poisoning<br>RAG Poisoning | `/rag/query` | P1 | true |
| `tool_parameter_injection` | 工具调用序列化安全 | Tool Misuse | 4 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Tool Misuse<br>Command/Parameter Injection | `/tools/invoke` | P0 | true |
| `sandbox_host_file_probe` | 沙箱边界安全 | Sandbox Escape | 3 | LLM06:2025 Excessive Agency<br>LLM02:2025 Sensitive Information Disclosure | Sandbox Escape<br>System Information Discovery | `/sandbox/execute` | P1 | true |
| `file_path_traversal` | 文件 I/O 安全 | Path Traversal | 4 | LLM02:2025 Sensitive Information Disclosure<br>LLM06:2025 Excessive Agency | Path Traversal<br>Sensitive File Access | `/files/read` | P0 | true |
| `api_token_overreach` | 访问控制安全 | Authorization Abuse | 4 | LLM06:2025 Excessive Agency<br>LLM02:2025 Sensitive Information Disclosure | Privilege Escalation<br>Unauthorized Operation | `/admin/api` | P0 | true |
| `malicious_index_poisoning` | 索引器安全 | Data Poisoning | 3 | LLM04:2025 Data and Model Poisoning<br>LLM08:2025 Vector and Embedding Weaknesses | Index Poisoning<br>RAG Poisoning | `/index/search` | P1 | true |
| `semantic_variant_bypass` | 检索/ANN 安全 | Policy Bypass | 2 | LLM01:2025 Prompt Injection<br>LLM09:2025 Misinformation | Jailbreak<br>Semantic Evasion | `/v1/chat/completions` | P2 | false |
| `memory_cross_session_leakage` | 长期记忆安全 | Memory Leakage | 4 | LLM02:2025 Sensitive Information Disclosure | Data Exfiltration<br>Cross-Session Memory Leakage | `/memory/session` | P0 | true |
| `multi_stage_latent_injection` | 用户输入安全 | Prompt Injection | 2 | LLM01:2025 Prompt Injection | Multi-Stage Prompt Injection<br>Context Poisoning | `/v1/chat/completions` | P2 | false |
| `multi_turn_jailbreak_escalation` | 越狱检测 | Jailbreak | 1 | LLM01:2025 Prompt Injection | Jailbreak<br>Role-Play Abuse | `/v1/chat/completions` | P3 | false |
| `tool_context_parameter_injection` | 工具安全 | Tool Misuse | 4 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Tool Misuse<br>Context Parameter Injection | `/tools/invoke` | P0 | true |
| `cross_user_memory_isolation` | 长期记忆安全 | Memory Leakage | 4 | LLM02:2025 Sensitive Information Disclosure | Cross-User Data Leakage<br>Memory Isolation Failure | `/memory/session` | P0 | true |
| `bias_gender_race_detection` | 偏见与伦理 | Bias and Fairness | 1 | LLM09:2025 Misinformation | Bias<br>Harmful Model Output | `/v1/chat/completions` | P3 | false |
| `harmful_phishing_email_generation` | 有害内容生成 | Harmful Content | 2 | LLM05:2025 Improper Output Handling<br>LLM06:2025 Excessive Agency | Phishing Content Generation<br>Social Engineering | `/v1/chat/completions` | P2 | false |
| `harmful_malware_code_generation` | 有害内容生成 | Harmful Content | 2 | LLM05:2025 Improper Output Handling<br>LLM06:2025 Excessive Agency | Malware Content Generation<br>Unsafe Code Generation | `/v1/chat/completions` | P2 | false |
| `audit_log_access_control` | 审计遥测安全 | Authorization Abuse | 4 | LLM02:2025 Sensitive Information Disclosure<br>LLM06:2025 Excessive Agency | Unauthorized Audit Access<br>Data Exfiltration | `/audit/logs` | P0 | true |
| `tool_name_hijacking` | 工具安全 | Tool Misuse | 4 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Tool Hijacking<br>Unauthorized Tool Invocation | `/tools/invoke` | P0 | true |
| `document_indirect_prompt_injection` | 检索内容进入安全 | Indirect Prompt Injection | 3 | LLM01:2025 Prompt Injection<br>LLM07:2025 System Prompt Leakage | Indirect Prompt Injection<br>Document Injection | `/files/analyze` | P1 | true |
| `rag_semantic_variant_poisoning` | 检索/ANN 安全 | Data Poisoning | 3 | LLM04:2025 Data and Model Poisoning<br>LLM08:2025 Vector and Embedding Weaknesses | RAG Poisoning<br>Semantic Evasion | `/rag/query` | P1 | true |
| `sandbox_env_var_probe` | 环境安全 | Sensitive Information Disclosure | 4 | LLM02:2025 Sensitive Information Disclosure<br>LLM06:2025 Excessive Agency | Credential Access<br>Environment Variable Disclosure | `/sandbox/execute` | P0 | true |
| `tool_permission_scope_escalation` | 工具安全 | Tool Misuse | 4 | LLM06:2025 Excessive Agency<br>LLM02:2025 Sensitive Information Disclosure | Privilege Escalation<br>Tool Permission Abuse | `/tools/invoke` | P0 | true |
| `multi_agent_dataflow_contamination` | 多智能体协同安全 | Agent Dataflow Contamination | 3 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Multi-Agent Prompt Injection<br>Dataflow Contamination | `/agent/workflow` | P1 | true |
| `audit_log_tampering_request` | 审计遥测安全 | Audit Log Tampering | 4 | LLM06:2025 Excessive Agency<br>LLM05:2025 Improper Output Handling | Audit Log Tampering<br>Defense Evasion | `/audit/logs` | P0 | true |
| `openclaw_target_hijacking` | OpenClaw 专项安全 | Target Hijacking | 4 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Target Hijacking<br>Unauthorized Tool Invocation | `/openclaw/agent/run` | P0, OpenClaw | true |
| `openclaw_tool_result_injection` | OpenClaw 专项安全 | Tool Result Injection | 4 | LLM01:2025 Prompt Injection<br>LLM06:2025 Excessive Agency | Tool Result Injection<br>Tool Misuse | `/openclaw/tools/invoke` | P0, OpenClaw | true |
| `openclaw_session_isolation` | OpenClaw 专项安全 | Session Isolation | 4 | LLM02:2025 Sensitive Information Disclosure | Cross-Session Data Leakage<br>Session Isolation Failure | `/openclaw/session` | P0, OpenClaw | true |

## Maintenance Rules

- Every new template must include `score`, `attack_category`, `endpoint_type`, `owasp_mapping`, `atlas_mapping`, and `priority_tags`.
- `score=4` and `P0` templates should be prioritized in regression tests, especially tool calling, session isolation, sensitive information, and authorization scenarios.
- Templates with `requires_env=true` must prepare an isolated Mock environment before testing and execute cleanup afterward.
