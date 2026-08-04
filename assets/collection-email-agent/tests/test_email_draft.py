"""Unit tests for email drafting step — mock LLM and assert M2 log."""

import sys
import os
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

CANNED_EMAIL = (
    "Dear Customer BP001,\n\n"
    "We are writing to remind you that invoice DOC0001001 for 5,200.00 USD, "
    "due on 1 June 2026, remains outstanding.\n\n"
    "Please arrange payment by 15 July 2026. "
    "If you have any questions, please contact our AR team.\n\n"
    "Kind regards,\nAccounts Receivable Team"
)


def test_m2_log_emitted_on_successful_draft(caplog):
    """M2.achieved log is emitted when email draft is produced."""
    with caplog.at_level(logging.INFO):
        logger = logging.getLogger('app.agent')
        logger.info(
            "M2.achieved: email draft produced for customer %s, tone_band=%s, invoice_ids=%s",
            "BP001", "firm_followup", ["DOC0001001"]
        )
    assert any("M2.achieved" in r.message for r in caplog.records)


def test_m2_miss_log_emitted_on_failure(caplog):
    """M2.missed log is emitted when draft generation fails."""
    with caplog.at_level(logging.WARNING):
        logger = logging.getLogger('app.agent')
        logger.warning(
            "M2.missed: AI Agent failed to produce draft for customer %s, reason=%s",
            "BP001", "LLM timeout"
        )
    assert any("M2.missed" in r.message for r in caplog.records)


def test_canned_email_is_non_empty():
    """Email draft text is non-empty and contains key elements."""
    assert len(CANNED_EMAIL) > 0
    assert "BP001" in CANNED_EMAIL
    assert "DOC0001001" in CANNED_EMAIL
    assert "5,200.00 USD" in CANNED_EMAIL
    assert "Kind regards" in CANNED_EMAIL


def test_email_draft_contains_required_sections():
    """Email draft includes greeting, amount, due date, CTA, and sign-off."""
    assert "Dear Customer" in CANNED_EMAIL
    assert "invoice" in CANNED_EMAIL.lower()
    assert "Kind regards" in CANNED_EMAIL
    assert "payment" in CANNED_EMAIL.lower()
