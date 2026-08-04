"""Unit tests for the tone_classifier module."""

import sys
import os
from datetime import date, timedelta

# Add app to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from tone_classifier import classify_tone_band


def test_not_overdue_same_day():
    """Invoice due today is not overdue."""
    today = date.today()
    assert classify_tone_band(today) == "not_overdue"


def test_not_overdue_future():
    """Invoice due in the future is not overdue."""
    future = date.today() + timedelta(days=5)
    assert classify_tone_band(future) == "not_overdue"


def test_polite_reminder_day_1():
    """Invoice 1 day overdue → polite reminder."""
    due = date.today() - timedelta(days=1)
    assert classify_tone_band(due) == "polite_reminder"


def test_polite_reminder_day_15():
    """Invoice 15 days overdue → polite reminder (boundary)."""
    due = date.today() - timedelta(days=15)
    assert classify_tone_band(due) == "polite_reminder"


def test_firm_followup_day_16():
    """Invoice 16 days overdue → firm follow-up (lower boundary)."""
    due = date.today() - timedelta(days=16)
    assert classify_tone_band(due) == "firm_followup"


def test_firm_followup_day_30():
    """Invoice 30 days overdue → firm follow-up (upper boundary)."""
    due = date.today() - timedelta(days=30)
    assert classify_tone_band(due) == "firm_followup"


def test_urgent_notice_day_31():
    """Invoice 31 days overdue → urgent notice (lower boundary)."""
    due = date.today() - timedelta(days=31)
    assert classify_tone_band(due) == "urgent_notice"


def test_urgent_notice_long_overdue():
    """Invoice 90 days overdue → urgent notice."""
    due = date.today() - timedelta(days=90)
    assert classify_tone_band(due) == "urgent_notice"
