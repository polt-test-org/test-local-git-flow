# Product Requirements Document (PRD)

**Title:** Personalized Collection Email Drafting Agent  
**Date:** 2026-07-23  
**Owner:** Finance / Accounts Receivable Team  
**Solution Category:** n8n Workflow, AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Collections specialists today spend valuable time manually writing overdue payment emails — often with inconsistent tone and urgency. This solution automatically drafts personalized collection emails from SAP S/4HANA data, letting specialists review and send in one click, and escalating unresolved cases to a manager automatically.

**Business Need:**  
The collections process relies on manual effort to compose emails for each overdue account. There is no systematic matching of email tone to the severity of the overdue situation, leading to inconsistent customer communication and delayed cash recovery. A scalable, AI-assisted drafting capability is needed.

**Expected Value:**  
- Reduce time spent per collection email from manual drafting to a single review-and-send action
- Improve consistency of customer communication by anchoring tone to overdue days
- Ensure no overdue account falls through the cracks through automated escalation

**Product Objectives (Prioritized):**
1. Automate email drafting so collections specialists only review and send — not write
2. Match email tone and urgency to the number of days the invoice is overdue
3. Escalate cases automatically to a manager when repeated collection attempts fail

---

## User Profiles & Personas

### Primary Persona: Alex — Collections Specialist

Alex is a 34-year-old accounts receivable specialist responsible for managing overdue customer accounts. Each morning he logs into S/4HANA, identifies overdue invoices, and manually writes collection emails. He handles 20–40 overdue accounts at a time and finds the repetitive writing time-consuming and inconsistent. He is comfortable using SAP and email tools but not a developer. He wants to spend his time on escalations and disputes — not writing first-contact emails. Success for Alex means a clean overdue queue at end of week.

### Secondary Persona: Maria — AR Manager / Team Lead

Maria is a 45-year-old AR team lead who oversees Alex and three other specialists. She is responsible for cash collection KPIs and needs visibility into accounts that have not responded after multiple collection attempts. She does not write collection emails herself but needs to be notified — and act — when cases escalate. Success for Maria means no high-value overdue accounts aging beyond 60 days without management engagement.

### Other User Types

- **S/4HANA System Administrator**: Manages API access and credentials for the S/4HANA integration.
- **IT/BTP Administrator**: Deploys and monitors the n8n workflow and AI Agent on SAP BTP.

---

## Goals and Non-Goals

### Goals (In Scope)

- Retrieve overdue invoices and customer data from SAP S/4HANA automatically
- Draft personalized collection emails with tone calibrated to days overdue (e.g., friendly reminder vs. urgent notice)
- Present draft emails to collections specialists for review before sending
- Track collection attempts per account and trigger manager escalation after a configurable threshold
- Notify the manager when escalation is triggered

### Non-Goals (Out of Scope)

- Automatically sending emails without specialist review
- Creating or modifying financial records in S/4HANA
- Managing disputes or payment plans
- Customer-facing self-service payment portal
- Multi-language email generation (initial release: single language)

---

## Requirements

### Must-Have Requirements

**REQ-01**: Retrieve Overdue Invoice Data from S/4HANA

- **Problem to Solve**: Specialists manually check S/4HANA for overdue accounts, which is time-consuming and error-prone.
- **User Story**: As a collections specialist, I need overdue invoices to be fetched automatically so that I can focus on reviewing and acting rather than searching.
- **Acceptance Criteria**:
  - Given a scheduled trigger fires, when the workflow runs, then all invoices overdue by more than a configurable number of days are retrieved from S/4HANA.
  - Given the data is retrieved, when the workflow continues, then each overdue item includes customer name, invoice number, amount, due date, and days overdue.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**REQ-02**: Draft Personalized Collection Email Based on Days Overdue

- **Problem to Solve**: Email tone is inconsistent and does not reflect the severity of the overdue situation.
- **User Story**: As a collections specialist, I need an AI-drafted email for each overdue account so that communication tone and content are appropriate to the situation.
- **Acceptance Criteria**:
  - Given an overdue invoice is identified, when the AI Agent is invoked, then a draft email is produced that addresses the customer by name, references the specific invoice(s), states the overdue amount and due date, and uses a tone appropriate to the days overdue band (e.g., 1–15 days: polite reminder; 16–30 days: firm follow-up; 30+ days: urgent notice).
  - Given the draft is produced, when it is presented to the specialist, then it is editable before sending.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 2

**REQ-03**: Collections Specialist Review and Send

- **Problem to Solve**: Specialists need to retain control over what is sent to customers.
- **User Story**: As a collections specialist, I need to review the AI-drafted email before it is sent so that I can correct errors and maintain professional communication standards.
- **Acceptance Criteria**:
  - Given a draft email is ready, when the specialist opens the review interface, then they can read, edit, approve, or discard the draft.
  - Given the specialist approves, when they confirm, then the email is dispatched to the customer.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 3

**REQ-04**: Automated Manager Escalation on Repeated Non-Payment

- **Problem to Solve**: High-value overdue accounts can be left unresolved if there is no escalation mechanism.
- **User Story**: As an AR manager, I need to be automatically notified when a customer has not responded after multiple collection attempts so that I can intervene before the debt ages further.
- **Acceptance Criteria**:
  - Given a configurable number of collection attempts (e.g., 3) have been made for an account without payment, when the threshold is reached, then the workflow sends an escalation notification to the responsible manager.
  - Given the escalation is triggered, when the manager receives the notification, then it includes account name, total overdue amount, number of attempts made, and dates of prior contacts.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 4

---

## Solution Architecture

**Architecture Overview:**  
The solution consists of two components: an **n8n Workflow** that orchestrates the end-to-end process (data retrieval, specialist review, escalation) and a **Python AI Agent** that handles personalized email drafting using SAP AI Core. The AI Agent exposes an A2A-compatible endpoint and is invoked by the n8n workflow as a sub-step.

**Key Components:**

- **n8n Workflow**: Scheduled trigger, S/4HANA data retrieval, AI Agent invocation, human-in-the-loop review step, escalation routing
- **Python AI Agent (A2A)**: Receives invoice and customer context, calls SAP AI Core LLM to generate a personalized email draft, returns the draft to n8n
- **SAP AI Core**: Provides the LLM runtime for email generation (e.g., GPT-4o via SAP Generative AI Hub)
- **MCP Tool / S/4HANA Integration**: MCP translation of the S/4HANA Dunning OData API (`CADUNNING_0001:v1`) used by the AI Agent to retrieve overdue item details
- **Review Interface**: A lightweight step within the n8n workflow (task/form node) presenting the draft to the collections specialist

**Integration Points:**

- **SAP S/4HANA (Dunning OData API)**: Read-only — retrieves overdue invoice data; polled on a configurable schedule
- **SAP AI Core / Generative AI Hub**: LLM inference for email generation; called per overdue account
- **Email system (SMTP / SAP BTP Mail)**: Outbound email dispatch once specialist approves

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The AI Agent is designed with configurable tone bands (days-overdue thresholds and corresponding tone labels) that can be extended without code changes
- Prompt templates for each tone band are externalised as configuration so the AR team can refine language without developer involvement
- The agent exposes a standard A2A endpoint so additional orchestrators (e.g., other n8n workflows or future CAP services) can invoke it

**Business Step Instrumentation:**
- All five key business milestones are instrumented with structured log statements
- Log pattern: `[MILESTONE_ID].[achieved|missed]: <description>`
- Observability is enabled via SAP AI Core telemetry and n8n execution logs

### Automation & Agent Behaviour

**Automation Level:** Hybrid — rule-based scheduling + AI-assisted drafting + human-in-the-loop approval

**Actions the system performs without human approval:**
- Retrieving overdue invoice data from S/4HANA on schedule
- Invoking the AI Agent to produce email drafts
- Sending escalation notifications to the manager when the attempt threshold is reached

**Actions that require human review or approval:**
- Sending a collection email to a customer (specialist must approve each draft)

**Model or engine used:** LLM via SAP Generative AI Hub (GPT-4o or equivalent); invoked by the Python AI Agent

**Knowledge & data sources accessed:**

- **SAP S/4HANA Dunning API**: Overdue invoices, customer names, amounts, due dates; read-only; owned by Finance

**Tools or connectors invoked:**

- **S/4HANA MCP Tool (Dunning)**: Read-only; fetches overdue invoice data for a customer
- **SAP AI Core LLM**: Generates email draft; no side effects
- **Email dispatch connector**: Write; sends approved email to customer

**Guardrails & fail-safes:**

- The agent never sends emails autonomously — all outbound emails require explicit specialist approval
- The agent does not create, modify, or delete any records in S/4HANA
- If the AI Agent returns an error or empty draft, the workflow flags the account for manual handling
- Escalation is capped at one notification per account per escalation cycle to prevent manager notification flooding

---

## Milestones

### M1: Overdue Invoice Detected

- **Description**: S/4HANA data is retrieved and one or more overdue invoices are identified for a customer account.
- **Achieved when**: At least one invoice exceeding the configured overdue threshold is returned from the Dunning API for a customer.
- **Log on achievement**: `M1.achieved: overdue invoices detected for customer {customer_id}, count={invoice_count}, max_days_overdue={max_days}`
- **Log on miss**: `M1.missed: no overdue invoices found for customer {customer_id} or data retrieval failed`

### M2: Email Drafted

- **Description**: The AI Agent produces a personalized email draft for the overdue account.
- **Achieved when**: The AI Agent returns a non-empty email draft containing customer name, invoice reference, and tone-appropriate content.
- **Log on achievement**: `M2.achieved: email draft produced for customer {customer_id}, tone_band={tone_band}, invoice_ids={invoice_ids}`
- **Log on miss**: `M2.missed: AI Agent failed to produce draft for customer {customer_id}, reason={error}`

### M3: Specialist Reviews Draft

- **Description**: The collections specialist opens the review interface and either approves, edits, or discards the draft.
- **Achieved when**: The specialist takes an explicit action (approve / edit+approve / discard) on the draft.
- **Log on achievement**: `M3.achieved: draft reviewed by specialist {user_id} for customer {customer_id}, action={action}`
- **Log on miss**: `M3.missed: draft not reviewed within SLA window for customer {customer_id}`

### M4: Email Sent

- **Description**: The approved collection email is dispatched to the customer.
- **Achieved when**: The email is successfully submitted to the mail system and a delivery confirmation is received.
- **Log on achievement**: `M4.achieved: collection email sent to customer {customer_id}, attempt_number={attempt_number}`
- **Log on miss**: `M4.missed: email dispatch failed for customer {customer_id}, reason={error}`

### M5: Escalation Triggered

- **Description**: The configurable attempt threshold is reached and the manager is notified.
- **Achieved when**: An escalation notification is sent to the responsible manager containing account details and attempt history.
- **Log on achievement**: `M5.achieved: escalation triggered for customer {customer_id}, total_attempts={attempts}, manager_notified={manager_id}`
- **Log on miss**: `M5.missed: escalation could not be sent for customer {customer_id}, reason={error}`

---

## Risks, Assumptions, and Dependencies

### Risks

- **LLM output quality**: AI-drafted emails may occasionally require significant editing; acceptance depends on prompt quality and tone band tuning.
- **S/4HANA API access**: The Dunning OData API must be accessible from BTP — network/firewall configuration may be required.
- **Escalation fatigue**: If thresholds are set too low, managers receive too many notifications; configurability is key.

### Assumptions

- SAP S/4HANA is the system of record for AR and dunning data and the Dunning OData API is enabled.
- SAP AI Core with Generative AI Hub access is provisioned on the BTP subaccount.
- Collections specialists have access to the n8n task review interface via their standard browser.
- A single escalation contact (manager) per AR team is sufficient for the initial release.

### Dependencies

- SAP S/4HANA Dunning OData API (`CADUNNING_0001:v1`) available and credentialed
- SAP AI Core / Generative AI Hub subscription active on BTP
- n8n instance running on SAP BTP (or accessible from BTP)
- Outbound email connectivity (SMTP or BTP Mail service)

---

## Appendix

### References

- SAP S/4HANA Contract Accounting Dunning API: `sap.s4:apiResource:CADUNNING_0001:v1`
- SAP S/4HANA Collections Management capability: SC100 (Public), SC5289 (Private)
- SAP AI Core documentation: https://help.sap.com/docs/sap-ai-core
- SAP BTP n8n integration guidance
