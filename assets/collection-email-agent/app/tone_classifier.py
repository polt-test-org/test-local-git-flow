"""Tone band classifier for collection emails based on days overdue."""

from datetime import date


def classify_tone_band(net_due_date: date) -> str:
    """Classify the email tone band based on days overdue.

    Args:
        net_due_date: The net due date of the invoice.

    Returns:
        One of: "polite_reminder", "firm_followup", "urgent_notice", "not_overdue"
    """
    today = date.today()
    days_overdue = (today - net_due_date).days

    if days_overdue <= 0:
        return "not_overdue"
    elif 1 <= days_overdue <= 15:
        return "polite_reminder"
    elif 16 <= days_overdue <= 30:
        return "firm_followup"
    else:
        return "urgent_notice"
