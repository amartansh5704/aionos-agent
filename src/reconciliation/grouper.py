"""
Groups extracted commitments and raw events by task identifier.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple
from src.schemas import ExtractedCommitment, NormalizedEvent

TASK_ALIASES = {
    "vendor_list": ["vendor list", "vendor", "raghav vendor"],
    "deck_review": ["q3 campaign deck", "deck review", "campaign deck", "deck"],
    "expense_report": ["expense variance report", "july expense", "expense report", "variance report", "expense"],
    "meridian_call": ["call reschedule", "meridian logistics", "meridian call", "meridian"],
    "mumbai_lease": ["mumbai office lease renewal", "mumbai lease", "mumbai office renewal", "mumbai renewal", "mumbai"],
}


def normalize_task_id(raw_task: str) -> str:
    cleaned = raw_task.lower().strip()
    for task_id, aliases in TASK_ALIASES.items():
        if cleaned == task_id or any(alias in cleaned for alias in aliases):
            return task_id
    return re.sub(r"\W+", "_", cleaned)


def group_commitments_by_task(
    commitments: List[ExtractedCommitment],
    events: List[NormalizedEvent],
) -> Dict[str, Tuple[List[ExtractedCommitment], List[NormalizedEvent]]]:
    grouped: Dict[str, Tuple[List[ExtractedCommitment], List[NormalizedEvent]]] = {}

    # Initialize standard tasks
    for task_id in TASK_ALIASES.keys():
        grouped[task_id] = ([], [])

    # Group extracted commitments
    for c in commitments:
        task_id = normalize_task_id(c.task)
        if task_id not in grouped:
            grouped[task_id] = ([], [])
        grouped[task_id][0].append(c)

    # Map raw events to task groups for context checking
    for e in events:
        text = (e.subject + " " + e.content).lower()
        matched = False
        for task_id, aliases in TASK_ALIASES.items():
            if any(alias in text for alias in aliases):
                grouped[task_id][1].append(e)
                matched = True
        if not matched and e.thread_id:
            tid = normalize_task_id(e.thread_id)
            if tid in grouped:
                grouped[tid][1].append(e)

    return grouped