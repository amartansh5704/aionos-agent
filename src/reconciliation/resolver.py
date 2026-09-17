"""
Reconciliation Engine: Resolves commitment drift by recency.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from src.schemas import (
    CommitmentVersion,
    Direction,
    ExtractedCommitment,
    NormalizedEvent,
    ReconciledCommitment,
    RiskStatus,
)
from src.reconciliation.grouper import group_commitments_by_task
from src.reconciliation.risk_classifier import classify_risk_status

TASK_LABELS = {
    "vendor_list": "Updated Vendor List for Raghav",
    "deck_review": "Q3 Campaign Deck Review with Neha",
    "expense_report": "July Expense Variance Report",
    "meridian_call": "Rescheduled Call with Meridian Logistics",
    "mumbai_lease": "Mumbai Office Lease Renewal Sign-off",
}


class ReconciliationEngine:
    def reconcile(
        self,
        commitments: List[ExtractedCommitment],
        events: List[NormalizedEvent],
        sim_now: datetime,
    ) -> List[ReconciledCommitment]:
        # Filter raw events up to sim_now
        visible_events = [e for e in events if e.timestamp <= sim_now]

        # Group commitments & events
        grouped = group_commitments_by_task(commitments, visible_events)
        reconciled: List[ReconciledCommitment] = []

        for task_id, (task_commitments, task_events) in grouped.items():
            # Filter commitments visible up to sim_now based on event source timestamp
            event_ts_map = {e.source_ref: e.timestamp for e in visible_events}
            visible_commitments = [
                c for c in task_commitments if c.source_ref in event_ts_map
            ]

            if not visible_commitments and not task_events:
                continue

            # Sort commitments chronologically by source timestamp
            visible_commitments.sort(key=lambda c: event_ts_map[c.source_ref])

            # Build version history
            history: List[CommitmentVersion] = []
            for c in visible_commitments:
                ts = event_ts_map[c.source_ref]
                history.append(
                    CommitmentVersion(
                        stated_deadline=c.stated_deadline,
                        stated_status=None,
                        source_ref=c.source_ref,
                        timestamp=ts,
                        raw_text=c.raw_text,
                    )
                )

            # Latest commitment statement wins (most-recent-wins rule)
            latest_c = visible_commitments[-1] if visible_commitments else None

            # Determine Owner and Direction
            owner = latest_c.owner if latest_c else "unassigned"
            direction = latest_c.direction if latest_c else Direction.UNOWNED
            counterparty = latest_c.counterparty if latest_c else None
            latest_ref = latest_c.source_ref if latest_c else (task_events[-1].source_ref if task_events else "")

            # Resolve current deadline by recency
            current_deadline = None
            for v in reversed(history):
                if v.stated_deadline:
                    current_deadline = v.stated_deadline
                    break

            # Classify Risk Status
            status, reason = classify_risk_status(
                task_id=task_id,
                owner=owner,
                direction=direction,
                current_deadline=current_deadline,
                events=task_events,
                sim_now=sim_now,
            )

            reconciled.append(
                ReconciledCommitment(
                    task_id=task_id,
                    task_label=TASK_LABELS.get(task_id, task_id.replace("_", " ").title()),
                    owner=owner,
                    counterparty=counterparty,
                    direction=direction,
                    current_deadline=current_deadline,
                    status=status,
                    status_reason=reason,
                    version_history=history,
                    latest_source_ref=latest_ref,
                )
            )

        return reconciled