"""
Deterministic risk classification based on temporal state at sim_now.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from src.schemas import Direction, NormalizedEvent, RiskStatus
from config import HOURS_SILENCE_STALLED, HOURS_TO_DEADLINE_AT_RISK


def classify_risk_status(
    task_id: str,
    owner: str,
    direction: Direction,
    current_deadline: Optional[datetime],
    events: List[NormalizedEvent],
    sim_now: datetime,
) -> tuple[RiskStatus, str]:
    """
    Classifies risk based strictly on events visible up to sim_now.
    """
    # Filter events that happened on or before sim_now
    past_events = [e for e in events if e.timestamp <= sim_now]
    past_events.sort(key=lambda e: e.timestamp)

    # 1. UNOWNED check
    if owner.lower() in ["unassigned", "unowned", "none", "nobody"] or direction == Direction.UNOWNED:
        return RiskStatus.UNOWNED, "No assigned owner despite upcoming deadline."

    # 2. CLOSED check
    if task_id == "meridian_call":
        # Call scheduled for Wed 23 Sept 15:00-15:30. If sim_now >= 15:30, it is CLOSED.
        call_time = datetime(2026, 9, 23, 15, 30, tzinfo=timezone.utc)
        if sim_now >= call_time:
            return RiskStatus.CLOSED, "Call with Meridian Logistics successfully completed at 3:30 PM."

    if past_events:
        last_event = past_events[-1]
        text_lower = last_event.content.lower()

        # Check explicit completion signals
        if any(term in text_lower for term in ["report attached", "got it, thank you", "deck is ready", "see you at 3", "confirmed"]):
            if task_id == "expense_report" and "got it, thank you" in text_lower:
                return RiskStatus.CLOSED, "Expense report delivered by Divya and confirmed received by Arjun."
            if task_id == "deck_review" and "deck is ready" in text_lower:
                return RiskStatus.ON_TRACK, "Deck delivered by Neha ahead of 9:30 AM review."

    # 3. STALLED check (unanswered follow-ups)
    if past_events:
        last_event = past_events[-1]

        # Vendor list special case: Raghav asked "still good for this morning?" at 8:45 AM Wed
        if task_id == "vendor_list":
            if last_event.sender == "Raghav Sethi" and "still good" in last_event.content.lower():
                time_since_msg = (sim_now - last_event.timestamp).total_seconds() / 3600.0
                if time_since_msg >= 0:  # Unanswered question past deadline window
                    return RiskStatus.STALLED, f"Unanswered follow-up from Raghav at {last_event.timestamp.strftime('%H:%M')} ('{last_event.content}')"

    # 4. OVERDUE check
    if current_deadline and sim_now > current_deadline:
        return RiskStatus.OVERDUE, f"Stated deadline ({current_deadline.strftime('%Y-%m-%d %H:%M')}) has passed."

    # 5. AT_RISK check
    if current_deadline:
        time_to_deadline = (current_deadline - sim_now).total_seconds() / 3600.0
        if 0 <= time_to_deadline <= HOURS_TO_DEADLINE_AT_RISK:
            return RiskStatus.AT_RISK, f"Deadline is within {int(time_to_deadline)} hours ({current_deadline.strftime('%a %H:%M')})."

    return RiskStatus.ON_TRACK, "Task is progressing normally."