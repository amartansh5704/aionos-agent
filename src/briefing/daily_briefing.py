"""
Daily Briefing Generator for Arjun Malhotra.
Renders commitments grouped by operational priority at a simulated time.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from src.schemas import BriefingSection, DailyBriefing, ReconciledCommitment, RiskStatus


class DailyBriefingGenerator:
    def generate_briefing(self, sim_now: datetime, reconciled: List[ReconciledCommitment]) -> DailyBriefing:
        overdue_stalled: List[ReconciledCommitment] = []
        arjun_owes: List[ReconciledCommitment] = []
        owes_arjun: List[ReconciledCommitment] = []
        unowned_escalations: List[ReconciledCommitment] = []
        closed_items: List[ReconciledCommitment] = []

        for item in reconciled:
            if item.status == RiskStatus.UNOWNED:
                unowned_escalations.append(item)
            elif item.status in [RiskStatus.OVERDUE, RiskStatus.STALLED]:
                overdue_stalled.append(item)
            elif item.status == RiskStatus.CLOSED:
                closed_items.append(item)
            elif item.direction.value == "arjun_owes":
                arjun_owes.append(item)
            else:
                owes_arjun.append(item)

        sections = [
            BriefingSection(
                heading="⚠️ Action Required / Overdue / Stalled",
                items=overdue_stalled,
            ),
            BriefingSection(
                heading="🚨 Unowned Escalations (Needs Ownership Assignment)",
                items=unowned_escalations,
            ),
            BriefingSection(
                heading="📋 What You (Arjun) Owe",
                items=arjun_owes,
            ),
            BriefingSection(
                heading="⏳ What Others Owe You",
                items=owes_arjun,
            ),
            BriefingSection(
                heading="✅ Recently Completed / Handled",
                items=closed_items,
            ),
        ]

        # Filter out empty sections
        active_sections = [s for s in sections if s.items]

        return DailyBriefing(
            sim_date=sim_now,
            sections=active_sections,
            unowned_alerts=unowned_escalations,
        )