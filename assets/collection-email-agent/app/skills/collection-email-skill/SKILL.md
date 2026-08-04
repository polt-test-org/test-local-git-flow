---
name: collection-email-skill
description: Instructions for drafting personalized collection emails based on dunning data from SAP S/4HANA
---

# Collection Email Drafting Rules

## Tone Band Classification

Use the `CANetDueDate` from the dunning item to calculate days overdue, then apply the tone band:

| Days Overdue | Tone Band | Approach |
|---|---|---|
| 1–15 days | Polite Reminder | Friendly, assume oversight, offer assistance |
| 16–30 days | Firm Follow-Up | Professional, firm, reference prior reminder |
| 30+ days | Urgent Notice | Serious tone, request immediate action |

## Email Structure

Each email MUST include the following sections in order:

1. **Greeting** — Address the customer by name using the BusinessPartner field (e.g., "Dear [Customer Name],")
2. **Reference** — Mention the specific invoice number(s) (CADocumentNumber) and contract account (ContractAccount)
3. **Outstanding Amount** — State the overdue amount (CADunningAmount or CADunningBalance) and currency (TransactionCurrency)
4. **Due Date** — State when payment was due (CANetDueDate) and how many days overdue
5. **Call to Action** — Request payment by a specific date (use CAPaymentTargetDate if available, else 7 days from today)
6. **Contact Info** — Ask the customer to contact the AR team if they have questions or disputes
7. **Sign-Off** — Professional close: "Kind regards, Accounts Receivable Team"

## Tone Examples

### Polite Reminder (1-15 days)
> We hope this message finds you well. We wanted to bring to your attention that invoice [number] for [amount] [currency], which was due on [date], remains outstanding. This may simply be an oversight — please arrange payment at your earliest convenience or contact us if you have any questions.

### Firm Follow-Up (16-30 days)
> This is a follow-up regarding invoice [number] for [amount] [currency], now [N] days overdue since [date]. Despite our previous reminder, we have not received payment. Please arrange settlement by [date] to avoid further action. If you are experiencing difficulties, please contact us to discuss options.

### Urgent Notice (30+ days)
> URGENT: Invoice [number] for [amount] [currency] is now [N] days overdue. Immediate payment is required. Failure to settle this balance by [date] may result in this account being referred for further action. Please contact our AR team immediately.

## Hard Rules

- NEVER threaten legal action or add penalty charges — these require management approval
- NEVER instruct the customer to pay via unofficial channels (e.g., personal bank transfers not in the system)
- NEVER include data not returned by the MCP tool — do not invent invoice numbers, amounts, or dates
- ALWAYS use only data from the CADunning and CADunningItem entities returned by the tool
- Address the customer by BusinessPartner ID if no name is available (e.g., "Dear Customer BP001,")
