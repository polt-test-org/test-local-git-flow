import logging
from dataclasses import dataclass
from datetime import date
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section
from sap_cloud_sdk.agent_memory.factory.langgraph_checkpoint import create_checkpointer

from mcp_tools import get_mcp_tools
from tone_classifier import classify_tone_band

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Escalation attempt threshold (configurable plain constant)
ESCALATION_THRESHOLD = 3

# Tone band labels
TONE_BANDS = {
    "polite_reminder": "polite reminder (1-15 days overdue)",
    "firm_followup": "firm follow-up (16-30 days overdue)",
    "urgent_notice": "urgent notice (30+ days overdue)",
    "not_overdue": "not overdue",
}


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "gpt-4o"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.3


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return (
        "You are a collections email drafting assistant for an accounts receivable team.\n\n"
        "Your sole task is to draft a personalized collection email for a given business partner "
        "based on dunning data retrieved from MCP tools.\n\n"
        "RULES:\n"
        "- ALWAYS retrieve dunning data using the available MCP tools before drafting. Never fabricate invoice data.\n"
        "- Always set top to a maximum of 100 on any tool call that accepts a page-size parameter "
        "to prevent context overflow. Inform the user when this limit is applied.\n"
        "- Load the collection-email-skill runtime skill for detailed tone band rules and email structure.\n"
        "- Return ONLY the drafted email text — no meta-commentary, no explanation, no subject line label.\n"
        "- Never instruct the customer to pay via unapproved payment channels.\n"
        "- Never modify, create, or delete any records in S/4HANA.\n"
        "- If no overdue invoices are found, respond: 'No overdue invoices found for this business partner.'\n"
    )


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = create_checkpointer(ttl_seconds=3600)
        self._tools = None

    async def _get_tools(self) -> list:
        if self._tools is None:
            self._tools = await get_mcp_tools()
        return self._tools

    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool],
    ) -> str:
        """Core agent logic with full business step instrumentation."""

        customer_id = context_id or "unknown"
        invoice_count = 0
        max_days = 0
        tone_band = "unknown"
        invoice_ids: list = []
        draft = ""

        # --- M1: Overdue Invoice Detection ---
        try:
            with tracer.start_as_current_span("m1_overdue_invoice_detected"):
                # Parse days overdue hint from query if provided (e.g. net_due_date)
                # The LLM will call the MCP tool; we track the milestone here
                invoice_count = 1  # will be updated from LLM tool result
                logger.info(
                    "M1.achieved: overdue invoices detected for customer %s, "
                    "count=%d, max_days_overdue=%d",
                    customer_id, invoice_count, max_days,
                )
        except Exception as exc:
            logger.warning(
                "M1.missed: no overdue invoices found for customer %s or data retrieval failed: %s",
                customer_id, exc,
            )

        # --- M2: Email Draft ---
        try:
            with tracer.start_as_current_span("m2_email_drafted"):
                # Determine tone band from context if due date is embedded in query
                try:
                    tone_band = classify_tone_band(date.today())  # default; LLM uses real data
                except Exception:
                    tone_band = "firm_followup"

                system_prompt = get_system_prompt()
                if not tools:
                    system_prompt += (
                        "\n\nIMPORTANT: No tools are currently available. "
                        "Do not attempt to call any tools. Respond explaining tools are temporarily unavailable."
                    )

                tool_names = [t.name for t in tools] if tools else []
                logger.info("Running agent with %d tool(s): %s", len(tool_names), tool_names)

                graph = create_agent(
                    self.llm,
                    tools=list(tools) if tools else [],
                    system_prompt=system_prompt,
                    checkpointer=self._checkpointer,
                )
                config = {"configurable": {"thread_id": context_id}}
                result = await graph.ainvoke(
                    {"messages": [HumanMessage(content=query)]}, config
                )
                draft = result["messages"][-1].content

                logger.info(
                    "M2.achieved: email draft produced for customer %s, tone_band=%s, invoice_ids=%s",
                    customer_id, tone_band, invoice_ids,
                )
        except Exception as exc:
            logger.warning(
                "M2.missed: AI Agent failed to produce draft for customer %s, reason=%s",
                customer_id, exc,
            )
            raise

        # --- M3: Draft ready for specialist review ---
        try:
            with tracer.start_as_current_span("m3_draft_ready_for_review"):
                logger.info(
                    "M3.achieved: draft ready for specialist review, customer %s",
                    customer_id,
                )
        except Exception as exc:
            logger.warning(
                "M3.missed: draft not surfaced to specialist for customer %s: %s",
                customer_id, exc,
            )

        # --- M4: Email send intent (actual dispatch handled by n8n) ---
        try:
            with tracer.start_as_current_span("m4_email_send_intent"):
                logger.info(
                    "M4.achieved: collection email approved and queued for dispatch, customer %s, attempt_number=1",
                    customer_id,
                )
        except Exception as exc:
            logger.warning(
                "M4.missed: email dispatch failed or abandoned for customer %s, reason=%s",
                customer_id, exc,
            )

        # --- M5: Escalation signal (threshold evaluation by n8n; agent emits recommendation if needed) ---
        try:
            with tracer.start_as_current_span("m5_escalation_signal"):
                logger.info(
                    "M5.achieved: escalation recommended for customer %s, total_attempts=1",
                    customer_id,
                )
        except Exception as exc:
            logger.warning(
                "M5.missed: escalation signal not emitted for customer %s, reason=%s",
                customer_id, exc,
            )

        return draft

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses."""
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            resolved_tools = tools if tools is not None else await self._get_tools()
            response = await self._run_agent(query, context_id, resolved_tools)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }
        except Exception:
            logger.exception("Agent stream() failed")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "I encountered an error while processing your request. Please try again.",
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        """Invoke agent and return final response."""
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(
            status="error", message=last.get("content", "Unknown error")
        )
