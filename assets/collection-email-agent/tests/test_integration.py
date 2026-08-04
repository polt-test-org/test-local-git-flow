"""Integration test: end-to-end agent flow with mocked LLM and MCP tools."""

import sys
import os
import logging
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Mock sap_cloud_sdk and mcp_tools BEFORE any agent imports
_mock_sdk = MagicMock()
sys.modules.setdefault('sap_cloud_sdk', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.aicore', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.core', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.core.telemetry', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.agent_decorators', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.agentgateway', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.agent_memory', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.agent_memory.factory', _mock_sdk)
sys.modules.setdefault('sap_cloud_sdk.agent_memory.factory.langgraph_checkpoint', _mock_sdk)
sys.modules.setdefault('langchain_litellm', MagicMock())
sys.modules.setdefault('langchain', MagicMock())

# Stub decorator functions that agent.py uses
_mock_sdk.agent_config = lambda **kw: (lambda fn: fn)
_mock_sdk.agent_model = lambda **kw: (lambda fn: fn)
_mock_sdk.prompt_section = lambda **kw: (lambda fn: fn)
_mock_sdk.create_checkpointer = MagicMock(return_value=MagicMock())
_mock_sdk.auto_instrument = MagicMock()
_mock_sdk.set_aicore_config = MagicMock()

# Mock mcp_tools module
_mock_mcp_tools = MagicMock()
_mock_mcp_tools.get_mcp_tools = AsyncMock(return_value=[])
sys.modules['mcp_tools'] = _mock_mcp_tools

# Mock langchain.agents.create_agent — ainvoke must be AsyncMock
_mock_langchain = MagicMock()
_fake_message = MagicMock()
_fake_message.content = (
    "Dear Customer BP001,\n\nWe are writing to remind you that invoice DOC0001001 "
    "for 5,200.00 USD, due on 1 June 2026, remains outstanding.\n\n"
    "Kind regards,\nAccounts Receivable Team"
)
_mock_graph = AsyncMock()
_mock_graph.ainvoke = AsyncMock(return_value={"messages": [_fake_message]})
_mock_langchain.create_agent = MagicMock(return_value=_mock_graph)
sys.modules['langchain.agents'] = _mock_langchain

CANNED_EMAIL = (
    "Dear Customer BP001,\n\n"
    "We are writing to remind you that invoice DOC0001001 for 5,200.00 USD, "
    "due on 1 June 2026, remains outstanding (22 days overdue).\n\n"
    "Please arrange immediate payment. Contact our AR team with any questions.\n\n"
    "Kind regards,\nAccounts Receivable Team"
)


@pytest.fixture
def mock_tools():
    """Return a list of mock LangChain-compatible tools."""
    tool = MagicMock()
    tool.name = "list_cadunning_for_sap_self"
    tool.description = "List overdue dunning records"
    return [tool]


@pytest.fixture
def mock_graph():
    """Return a mock LangGraph agent graph with async ainvoke."""
    fake_message = MagicMock()
    fake_message.content = CANNED_EMAIL
    graph = AsyncMock()
    graph.ainvoke = AsyncMock(return_value={"messages": [fake_message]})
    return graph


@pytest.mark.asyncio
async def test_agent_invoke_returns_non_empty_draft(mock_tools, mock_graph, caplog):
    """Agent invoke returns a non-empty email draft when LLM is mocked."""

    with caplog.at_level(logging.INFO), \
         patch("app.agent.create_agent", return_value=mock_graph), \
         patch("app.agent.create_checkpointer", return_value=MagicMock()):

        import importlib
        import app.agent as agent_mod
        importlib.reload(agent_mod)

        agent = agent_mod.SampleAgent()
        response = await agent.invoke(
            query="Draft collection email for BusinessPartner BP001",
            context_id="BP001-000001",
            tools=mock_tools,
        )

    assert response.status == "completed"
    assert len(response.message) > 0
    assert "BP001" in response.message


@pytest.mark.asyncio
async def test_m1_and_m2_logs_emitted(mock_tools, mock_graph, caplog):
    """M1 and M2 milestone logs are emitted during agent execution."""

    with caplog.at_level(logging.INFO), \
         patch("app.agent.create_agent", return_value=mock_graph), \
         patch("app.agent.create_checkpointer", return_value=MagicMock()):

        import importlib
        import app.agent as agent_mod
        importlib.reload(agent_mod)

        agent = agent_mod.SampleAgent()
        await agent.invoke(
            query="Draft collection email for BusinessPartner BP001",
            context_id="BP001-000001",
            tools=mock_tools,
        )

    log_messages = [r.message for r in caplog.records]
    assert any("M1.achieved" in msg for msg in log_messages), \
        f"M1.achieved not found in logs: {log_messages}"
    assert any("M2.achieved" in msg for msg in log_messages), \
        f"M2.achieved not found in logs: {log_messages}"
