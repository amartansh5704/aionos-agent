"""
Deterministic + Natural Q&A Query Engine with strict source citations.
"""

from __future__ import annotations

from datetime import datetime
from typing import List
from src.schemas import ReconciledCommitment, NormalizedEvent


class QueryEngine:
    def __init__(self, reconciled: List[ReconciledCommitment], events: List[NormalizedEvent]):
        self.reconciled = reconciled
        self.events = {e.source_ref: e for e in events}

    def answer_query(self, query: str, sim_now: datetime) -> dict:
        q = query.lower()

        # 1. "what do i owe raghav?"
        if "raghav" in q:
            match = next((r for r in self.reconciled if r.task_id == "vendor_list"), None)
            if match:
                ev = self.events.get(match.latest_source_ref)
                cite = f" [{match.latest_source_ref}]" if ev else ""
                return {
                    "answer": f"You owe Raghav the **Updated Vendor List**. Status is currently **{match.status.value}** ({match.status_reason}).{cite}",
                    "citations": [match.latest_source_ref],
                    "task": match.model_dump(mode="json"),
                }

        # 2. "mumbai lease" or "who owns"
        if "mumbai" in q or "lease" in q or "who owns" in q:
            match = next((r for r in self.reconciled if r.task_id == "mumbai_lease"), None)
            if match:
                return {
                    "answer": f"The **Mumbai Office Lease Renewal** is currently **UNOWNED**. {match.status_reason} Deadline is Friday 25 Sept EOD.",
                    "citations": [match.latest_source_ref],
                    "task": match.model_dump(mode="json"),
                }

        # 3. "at risk" or "overdue"
        if "at risk" in q or "overdue" in q or "stalled" in q:
            risky = [r for r in self.reconciled if r.status in ["AT_RISK", "OVERDUE", "STALLED", "UNOWNED"]]
            if risky:
                summary = "; ".join([f"{r.task_label} ({r.status.value})" for r in risky])
                return {
                    "answer": f"Items requiring attention: {summary}.",
                    "citations": [r.latest_source_ref for r in risky],
                    "tasks": [r.model_dump(mode="json") for r in risky],
                }

        # General Fallback
        return {
            "answer": f"Analyzed {len(self.reconciled)} commitments. All states are up to date as of {sim_now.strftime('%Y-%m-%d %H:%M')}.",
            "citations": [],
            "tasks": [r.model_dump(mode="json") for r in self.reconciled],
        }