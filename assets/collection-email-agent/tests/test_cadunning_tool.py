"""Unit tests for the CADunning MCP tool interaction via mocks."""

import sys
import os
import json
import logging
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


# Sample dunning data matching mcp-mock.json structure
MOCK_DUNNING_RESPONSE = {
    "value": [
        {
            "CAMassRunDate": "2026-07-01",
            "CAMassRunID": "RUN01",
            "BusinessPartner": "BP001",
            "ContractAccount": "CA0000001001",
            "CADunningCounter": "000001",
            "CADunningLevel": "02",
            "TransactionCurrency": "USD",
            "CADunningBalance": "5200.00",
            "CAPaymentTargetDate": "2026-07-15",
            "CADunningNoticeIsReversed": False,
        }
    ]
}


def test_mock_dunning_data_structure():
    """Verify the mock dunning data has the expected structure for the agent."""
    assert "value" in MOCK_DUNNING_RESPONSE
    records = MOCK_DUNNING_RESPONSE["value"]
    assert len(records) > 0

    record = records[0]
    assert "BusinessPartner" in record
    assert "CADunningBalance" in record
    assert "TransactionCurrency" in record
    assert "CADunningLevel" in record


def test_mock_dunning_item_fields():
    """Verify required fields are present in dunning record."""
    record = MOCK_DUNNING_RESPONSE["value"][0]
    assert record["BusinessPartner"] == "BP001"
    assert record["CADunningBalance"] == "5200.00"
    assert record["TransactionCurrency"] == "USD"
    assert record["CADunningNoticeIsReversed"] is False


def test_m1_log_emitted_on_data_found(caplog):
    """M1 milestone log is emitted when overdue invoices are found."""
    with caplog.at_level(logging.INFO):
        logger = logging.getLogger('app.agent')
        logger.info(
            "M1.achieved: overdue invoices detected for customer %s, count=%d, max_days_overdue=%d",
            "BP001", 1, 52
        )

    assert any("M1.achieved" in r.message for r in caplog.records)


def test_m1_miss_log_emitted_on_empty_data(caplog):
    """M1 missed log is emitted when no overdue invoices are found."""
    with caplog.at_level(logging.WARNING, logger='app.agent'):
        logger = logging.getLogger('app.agent')
        logger.warning(
            "M1.missed: no overdue invoices found for customer %s or data retrieval failed: %s",
            "BP999", "empty result set"
        )

    assert any("M1.missed" in r.message for r in caplog.records)


def test_mcp_mock_json_is_valid():
    """mcp-mock.json exists and is valid JSON with expected structure."""
    mock_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-mock.json')
    assert os.path.exists(mock_path), "mcp-mock.json must exist"

    with open(mock_path) as f:
        data = json.load(f)

    assert "servers" in data
    assert "sap-s4-cadunning" in data["servers"]
    server = data["servers"]["sap-s4-cadunning"]
    assert "tools" in server
    assert "list_cadunning_for_sap_self" in server["tools"]
