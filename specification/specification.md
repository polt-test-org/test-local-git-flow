# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [x] Create asset directories: `mkdir -p assets/collection-email-agent/ assets/n8n/`
- [x] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for every asset
- [x] Validate all `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [x] Execute specification/collection-email-agent/specification.md (all items)
- [x] Execute specification/n8n/specification.md (all items)
- [x] Cross-implementation compatibility check — verify the following before marking complete:
  - The n8n workflow HTTP Request node that invokes the agent uses a `POST` body with `query` and `context_id` fields matching what the agent's `stream()` / `invoke` endpoint expects
  - The agent's A2A endpoint returns a JSON response that the n8n workflow can parse to extract the drafted email text
  - Both assets use consistent field names for the BusinessPartner identifier (`BusinessPartner`)
  - The dunning MCP server ORD ID in `assets/collection-email-agent/asset.yaml` `requires` block matches the ORD ID registered during `setup-solution` for the MCP server asset
  - Environment variable names used in the agent match what is documented for SAP AI Core / LiteLLM at runtime
