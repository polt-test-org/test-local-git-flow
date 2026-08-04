# Specification: collection-email-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` from the project root
- [ ] Bootstrap agent code in `assets/collection-email-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/collection-email-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skill: Collection Email Drafting

- [ ] Create runtime skill `assets/collection-email-agent/app/skills/collection-email-skill/SKILL.md` with:
  - Frontmatter: `name: collection-email-skill`, `description: Instructions for drafting personalized collection emails based on dunning data`
  - Body: tone band rules (1–15 days overdue → polite reminder; 16–30 days → firm follow-up; 30+ days → urgent notice), email structure (greeting, invoice reference, outstanding amount, due date, call to action, sign-off), instruction to never threaten legal action or add penalty charges autonomously, instruction to always address the customer by name using the BusinessPartner field, instruction never to hallucinate invoice data — use only data from the MCP tool response

---

## Agent System Prompt & LLM Configuration

- [ ] In `assets/collection-email-agent/app/agent.py`:
  - Set the `@agent_model` decorator to use `gpt-4o` (via SAP AI Core / LiteLLM)
  - Set the `@agent_config` decorator with `temperature=0.3` (low temperature for consistent professional tone)
  - Implement the `@prompt_section` decorated function to return the system prompt:
    - Role: "You are a collections email drafting assistant for an accounts receivable team."
    - Instruction: use dunning data retrieved from MCP tools (do not hallucinate invoice data)
    - Instruction: always set `top` to a maximum of 100 on any tool call that accepts a page-size parameter to prevent context overflow; inform the user when this limit is applied
    - Instruction: classify the email tone by days overdue (calculated from `CANetDueDate` on each dunning item); load the `collection-email-skill` runtime skill for detailed tone rules
    - Instruction: return only the drafted email text — no meta-commentary, no explanation
    - Guardrail: never instruct the customer to pay via unapproved payment channels; never modify financial records; never send emails autonomously

---

## Core Agent Logic

- [ ] In `assets/collection-email-agent/app/agent.py`, implement the main `_run_agent()` async method (extracted from `stream()`) that:
  1. Accepts `query` (natural language request from n8n, e.g. "Draft collection email for BusinessPartner BP001") and `context_id`
  2. Loads MCP tools via `get_mcp_tools()` from `mcp_tools.py`
  3. Builds the LangGraph agent graph with the loaded tools and system prompt
  4. Invokes the graph with the query
  5. Returns the drafted email text as a string
- [ ] Implement `stream()` to call `_run_agent()` and yield the result — do NOT use `with tracer.start_as_current_span(...)` as a context manager inside `stream()` (async generator restriction); all span instrumentation goes inside `_run_agent()`

---

## MCP Tool Wiring (S/4HANA Dunning API)

- [ ] Verify `specification/collection-email-agent/api-specs/cadunning.edmx` exists (already downloaded)
- [ ] Invoke `mcp-translation-file` skill to generate MCP translation from `specification/collection-email-agent/api-specs/cadunning.edmx`
  - API ORD ID: `sap.s4:apiResource:CADUNNING_0001:v1`
  - API type: `edmx`
- [ ] Invoke `setup-solution` skill to register the generated MCP server asset (one MCP asset for the dunning API)
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from `mcp_tools.py` (canonical pattern from guidelines-agent.md) — NEVER create direct HTTP clients (`requests`, `httpx`, OData client)
- [ ] Add the dunning MCP server to `assets/collection-email-agent/asset.yaml` under `requires`:
  ```yaml
  requires:
    - name: cadunning-mcp-server
      kind: mcp-server
      ordId: sap.s4:apiResource:CADUNNING_0001:v1
  ```
- [ ] Invoke `mcp-mock-config` skill to generate `mcp-mock.json` for tests (must run AFTER `mcp-translation-file` and `setup-solution`)

---

## Business Step Instrumentation (Milestones)

- [ ] Implement all 5 milestones from the PRD in `_run_agent()` using structured logging + OpenTelemetry spans (decorator or context manager form — never inside async generator):

  **M1 — Overdue Invoice Detected**
  - Span: `m1_overdue_invoice_detected`
  - Log on achievement: `M1.achieved: overdue invoices detected for customer {customer_id}, count={invoice_count}, max_days_overdue={max_days}`
  - Log on miss: `M1.missed: no overdue invoices found for customer {customer_id} or data retrieval failed`

  **M2 — Email Drafted**
  - Span: `m2_email_drafted`
  - Log on achievement: `M2.achieved: email draft produced for customer {customer_id}, tone_band={tone_band}, invoice_ids={invoice_ids}`
  - Log on miss: `M2.missed: AI Agent failed to produce draft for customer {customer_id}, reason={error}`

  **M3 — Specialist Reviews Draft** *(logged by n8n workflow; agent emits a readiness signal)*
  - Log on achievement: `M3.achieved: draft ready for specialist review, customer {customer_id}`
  - Log on miss: `M3.missed: draft not surfaced to specialist for customer {customer_id}`

  **M4 — Email Sent** *(dispatched by n8n; agent emits intent signal)*
  - Log on achievement: `M4.achieved: collection email approved and queued for dispatch, customer {customer_id}, attempt_number={attempt_number}`
  - Log on miss: `M4.missed: email dispatch failed or abandoned for customer {customer_id}, reason={error}`

  **M5 — Escalation Triggered** *(handled by n8n; agent emits escalation recommendation)*
  - Log on achievement: `M5.achieved: escalation recommended for customer {customer_id}, total_attempts={attempts}`
  - Log on miss: `M5.missed: escalation signal not emitted for customer {customer_id}, reason={error}`

- [ ] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

---

## Tone Band Helper

- [ ] Implement a pure Python helper function `classify_tone_band(net_due_date: date) -> str` in a new module `assets/collection-email-agent/app/tone_classifier.py`:
  - `days_overdue = (today - net_due_date).days`
  - Returns `"polite_reminder"` if 1 ≤ days_overdue ≤ 15
  - Returns `"firm_followup"` if 16 ≤ days_overdue ≤ 30
  - Returns `"urgent_notice"` if days_overdue > 30
  - Returns `"not_overdue"` if days_overdue ≤ 0
- [ ] Import and use `classify_tone_band` in `_run_agent()` to include the tone band in the LLM prompt context

---

## Agent Cleanup

- [ ] Delete the template runtime skill: `rm -rf assets/collection-email-agent/app/skills/template-skill/`
- [ ] Verify `assets/collection-email-agent/app/agent.py` has exactly 3 decorated functions (`@agent_model`, `@agent_config`, `@prompt_section`) — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/collection-email-agent/app/agent.py` and confirm it returns 3

---

## Testing

- [ ] `conftest.py` only sets `IBD_TESTING=true` — the fixture monkey-patches `mcp_tools.get_mcp_tools` to return mock tools built from `mcp-mock.json`
- [ ] Write unit tests in `assets/collection-email-agent/tests/`:
  - `test_tone_classifier.py` — unit tests for all four `classify_tone_band` outcomes (polite_reminder, firm_followup, urgent_notice, not_overdue); run immediately after writing
  - `test_cadunning_tool.py` — unit test for the dunning MCP tool call (mock tool returns sample `CADunning` + `CADunningItem` data; assert M1 log is emitted); run immediately after writing
  - `test_email_draft.py` — unit test for the email drafting step (mock LLM returns canned email text; assert M2 log is emitted and draft is non-empty); run immediately after writing
- [ ] Write one integration test `assets/collection-email-agent/tests/test_integration.py`:
  - Calls the agent's `invoke` function end-to-end with a sample query (`"Draft collection email for BusinessPartner BP001"`)
  - Mocks `mcp_tools.get_mcp_tools` (returns mock dunning tool) and mocks `ChatLiteLLM` (returns canned email)
  - Asserts the response contains a non-empty email draft
  - Asserts M1 and M2 log messages are emitted
- [ ] Run `pytest` from `assets/collection-email-agent/` (no args) — if coverage < 70%, add targeted tests
- [ ] Verify `assets/collection-email-agent/app/agent.py` has exactly 3 decorated functions (grep check above)
- [ ] Run `pytest` again from `assets/collection-email-agent/` (no args) to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/collection-email-agent/`
