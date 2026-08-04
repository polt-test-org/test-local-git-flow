# Specification: n8n (Collection Email Orchestration Workflow)

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-n8n-workflow.md](../guidelines-n8n-workflow.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md` from the project root
- [ ] Create directory `assets/n8n/workflows/` for all workflow JSON files

---

## Workflow: Collection Email Orchestration

**File**: `assets/n8n/workflows/collection-email-orchestration.n8n.json`

Implement a single n8n workflow with the following node chain. Use the `n8n-workflow` skill to generate the JSON.

### Nodes to implement (in order):

**1. Schedule Trigger**
- Node type: Schedule Trigger
- Runs daily (e.g. every weekday at 8:00 AM)
- Purpose: kicks off the overdue invoice check each business day

**2. Fetch Overdue Invoices (HTTP Request)**
- Node type: HTTP Request
- Method: GET
- URL placeholder: `https://your-s4hana-system.com/sap/opu/odata4/sap/api_cadunning/srvd_a2x/sap/api_cadunning/0001/CADunning?$filter=CADunningNoticeIsReversed eq false&$top=100`
- Purpose: retrieves current dunning header records from S/4HANA
- Leave authentication unconfigured (user assigns credentials in n8n UI)
- Map output: pass `value` array to next node

**3. Split Into Batches (Split In Batches)**
- Node type: Split In Batches
- Batch size: 1 (process one business partner at a time)
- Purpose: iterate over each overdue account individually

**4. Invoke Collection Email Agent (HTTP Request)**
- Node type: HTTP Request
- Method: POST
- URL placeholder: `https://agent.company.com/api` (configurable — do NOT use environment variables like `$env.*`)
- Body (JSON):
  ```json
  {
    "query": "Draft collection email for BusinessPartner {{ $json.BusinessPartner }} with dunning balance {{ $json.CADunningBalance }} {{ $json.TransactionCurrency }}, dunning level {{ $json.CADunningLevel }}, next dunning date {{ $json.CANextDunningDate }}",
    "context_id": "{{ $json.BusinessPartner }}-{{ $json.CADunningCounter }}"
  }
  ```
- Purpose: calls the AI Agent to produce a personalized email draft for the current business partner
- Leave authentication unconfigured

**5. Wait for Specialist Review (Wait)**
- Node type: Wait
- Resume: on webhook (provides a review URL)
- Purpose: human-in-the-loop pause — the workflow pauses and sends a review notification; resumes when the specialist approves or discards

**6. Send Review Notification (Send Email or HTTP Request)**
- Node type: Send Email (or HTTP Request to a notification endpoint)
- To: placeholder `collections-team@company.com`
- Subject: `[Action Required] Collection Email Draft — {{ $json.BusinessPartner }}`
- Body: include the AI-drafted email text and the resume webhook URL so the specialist can click to approve
- Purpose: notifies the collections specialist that a draft is ready for review
- Leave authentication unconfigured

**7. Check Specialist Decision (IF)**
- Node type: IF
- Condition: `{{ $json.action }}` equals `"approve"`
- True branch → Send Email node
- False branch → Log Discarded node

**8. Send Collection Email (Send Email)**
- Node type: Send Email
- To: placeholder — use `{{ $json.customerEmail }}` (supplied by specialist in the approval webhook payload, or fetched from S/4HANA in an earlier step)
- Subject: `Payment Reminder — Invoice {{ $json.invoiceNumber }}`
- Body: the approved email draft text from the agent response
- Purpose: dispatches the final approved email to the customer
- Leave authentication unconfigured

**9. Log Discarded (Set)**
- Node type: Set
- Purpose: records that the draft was discarded by the specialist (sets `status = "discarded"`)

**10. Increment Attempt Counter (Set)**
- Node type: Set
- Purpose: increments `collectionAttemptCount` for the current BusinessPartner (use a static data store node or a simple Set node that reads from workflow static data)
- After send: set `collectionAttemptCount = {{ ($json.collectionAttemptCount || 0) + 1 }}`

**11. Check Escalation Threshold (IF)**
- Node type: IF
- Condition: `{{ $json.collectionAttemptCount }}` greater than or equal to `3` (configurable threshold)
- True branch → Escalate to Manager node
- False branch → End (no escalation needed)

**12. Escalate to Manager (Send Email)**
- Node type: Send Email
- To: placeholder `ar-manager@company.com`
- Subject: `[Escalation] Unresolved Overdue Account — {{ $json.BusinessPartner }}`
- Body: include customer name, total dunning balance, currency, number of collection attempts, and dates of prior contacts
- Purpose: notifies the AR manager that the account requires management intervention
- Leave authentication unconfigured

### Workflow-level requirements:
- [ ] All node `connections` reference other nodes by `name`, not `id`
- [ ] No `"credentials"` blocks in any node
- [ ] No `"authentication"` or `"genericAuthType"` parameters on HTTP Request nodes
- [ ] Agent URL uses a plain placeholder string (`https://agent.company.com/api`) — not `$env.*` variables
- [ ] Workflow JSON is valid and well-formed

---

## Asset YAML

- [ ] Invoke `setup-solution` skill to create `assets/n8n/asset.yaml` with `sourceRoot: workflows`

---

## Validation

- [ ] Run n8n workflow validation: `n8n-mcp__validate-n8n-workflow` with the generated JSON
- [ ] Confirm JSON is well-formed: `cat assets/n8n/workflows/collection-email-orchestration.n8n.json | python3 -m json.tool > /dev/null && echo "valid JSON"`
- [ ] Confirm no `"credentials"` key appears in the workflow: `grep -c '"credentials"' assets/n8n/workflows/collection-email-orchestration.n8n.json` should return 0
