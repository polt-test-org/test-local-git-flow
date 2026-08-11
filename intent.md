# Personalized Collection Email Drafting Agent
add hello!
add hello 22222
AI-powered agent that drafts tailored collection emails based on customer payment history and outstanding invoices, with manager escalation for repeat non-payment.

## Business challenge

Collections specialists spend significant time manually crafting collection emails for overdue accounts. The process is inconsistent — email tone and urgency are not always matched to the customer's overdue status. This agent drafts personalized collection emails based on how many days an invoice is overdue, surfaces them to the collections specialist for review and send, and escalates to a manager when repeated non-payment occurs.

## Key Milestones

1. **Overdue Invoice Detected** — S/4HANA data is retrieved and overdue items are identified for a customer
2. **Email Drafted** — AI agent produces a personalized email with appropriate tone based on days overdue
3. **Specialist Reviews Draft** — Collections specialist reviews the draft in a UI and decides to send or edit
4. **Email Sent** — Final email is dispatched to the customer
5. **Escalation Triggered** — If non-payment persists after a defined number of attempts, the case is escalated to a manager

## Business Architecture (RBA)

### End-to-End Process

Finance — Invoice to Cash (generic)

### Process Hierarchy

```
Finance (E2E)
└── Invoice to Cash (generic)
    └── Process accounts receivables and collect payment (BPS-366)
        └── Process accounts receivable (AR)
        └── Manage receivables financing
```

### Summary

The business challenge maps directly to "Process accounts receivables and collect payment" (BPS-366) within the Invoice to Cash phase of the Finance E2E process. The AI agent augments the standard AR collections workflow with intelligent, context-aware email drafting and escalation logic.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ---- | ------------------- |
| Read overdue invoices and dunning data from S/4HANA | SAP S/4HANA Collections Management (SC100 / SC5289) | `sap.s4:apiResource:CADUNNING_0001:v1` | — | — | No | OData EDMX available; no MCP server found — API will be wrapped via MCP translation |
| Retrieve customer payment history | SAP S/4HANA Open Item Management (SC5084 / SC3503) | — | — | — | Maybe | No direct OData ORD ID confirmed; may need custom query or dunning API extension |
| Determine email tone based on days overdue | Not covered by standard SAP product | — | — | — | Yes | Custom AI logic required — AI Agent will implement tone classification |
| Draft personalized collection email | Not covered by standard SAP product | — | — | — | Yes | Pro-code Python AI Agent using SAP AI Core LLM |
| Collections specialist review UI | Not covered by standard SAP product | — | — | — | Yes | Lightweight review interface needed; CAP + React frontend or n8n task node |
| Escalate to manager after repeated non-payment | SAP S/4HANA Collections Management (behavioral insights SC6130) | — | — | — | Yes | No native email-based escalation; n8n workflow will handle escalation routing |

### Key findings

- SAP S/4HANA provides the data layer (dunning, open items, AR) but does not offer AI-driven email drafting natively.
- The Dunning OData API (`CADUNNING_0001:v1`) is the primary data source for overdue invoice data; it will be wrapped as an MCP tool.
- Email personalization based on days overdue and escalation logic are custom gaps — best addressed by a Python AI Agent + n8n Workflow combination.
- The collections specialist needs a review step before emails are sent; this is handled as a human-in-the-loop step in the n8n workflow.
- No MCP servers were found for the relevant S/4HANA APIs — MCP translation files will be generated from the EDMX specs.
- The solution follows a well-established pattern: n8n handles orchestration and escalation; the AI Agent handles context-aware email composition.

## Recommendations

### AI Agent + n8n Workflow for Collections Email Drafting and Escalation

#### Executive Summary

n8n workflow orchestrates the end-to-end process; AI Agent drafts personalized emails.

#### Recommended Solution

Build an n8n workflow that periodically queries SAP S/4HANA for overdue AR items, invokes a Python AI Agent (connected to SAP AI Core) to draft a personalized collection email tailored to the number of days overdue, and presents the draft to the collections specialist for review and send. If non-payment persists after a configurable number of attempts, the workflow escalates the case to a manager via notification.

The AI Agent uses MCP tools generated from the S/4HANA Dunning OData API to retrieve invoice and customer data, and SAP AI Core for LLM-based email generation.

#### Recommended solution category

n8n Workflow, AI Agent

#### Intent fit
92%
