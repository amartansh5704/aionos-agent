"""
Pydantic v2 schemas — the single source of truth for every data
structure that flows through the pipeline.

Design choices:
  - Every record carries a `source_ref` so the briefing can cite
    exactly which email / meeting minute / voice note produced it.
  - Timestamps are always timezone-aware ISO-8601 strings.
  - The `Commitment` model has a `version_history` list so the
    reconciliation engine can show *how* a deadline drifted.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────

class SourceType(str, Enum):
    MEETING = "meeting"
    CALENDAR = "calendar"
    EMAIL = "email"
    VOICE_NOTE = "voice_note"


class RiskStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    STALLED = "STALLED"
    OVERDUE = "OVERDUE"
    UNOWNED = "UNOWNED"
    CLOSED = "CLOSED"


class Direction(str, Enum):
    """Who owes whom, relative to Arjun."""
    ARJUN_OWES = "arjun_owes"          # Arjun → counterparty
    OWES_ARJUN = "owes_arjun"          # counterparty → Arjun
    UNOWNED = "unowned"                # no clear owner
    INTERNAL_REMINDER = "internal"     # Arjun → Arjun (voice note)


# ── Layer 1: Normalized Event (output of ingestion) ──────────

class NormalizedEvent(BaseModel):
    """One atomic message / calendar entry / transcript segment."""
    source_type: SourceType
    timestamp: datetime
    sender: str                         # person name or "Facilities"
    recipients: list[str] = Field(default_factory=list)
    subject: str = ""                   # email subject or meeting title
    content: str                        # body text
    source_ref: str                     # e.g. "email:thread_vendor_list:msg_5"
    thread_id: Optional[str] = None     # groups emails in same thread


# ── Layer 2: Extracted Commitment (output of LLM extraction) ─

class CommitmentVersion(BaseModel):
    """One snapshot of a commitment as stated at a point in time."""
    stated_deadline: Optional[datetime] = None
    stated_status: Optional[str] = None  # e.g. "confirmed", "rescheduled"
    source_ref: str
    timestamp: datetime                 # when this version was stated
    raw_text: str = ""                  # verbatim excerpt


class ExtractedCommitment(BaseModel):
    """A single commitment candidate pulled from one source record."""
    task: str                           # short label: "vendor list", "deck review"
    owner: str                          # person name or "unassigned"
    counterparty: Optional[str] = None
    direction: Direction
    stated_deadline: Optional[datetime] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    source_ref: str
    raw_text: str = ""


# ── Layer 3: Reconciled Commitment (output of resolver) ──────

class ReconciledCommitment(BaseModel):
    """The current, deduplicated, conflict-resolved state of a task."""
    task_id: str                        # slug: "vendor_list", "mumbai_lease"
    task_label: str                     # human-readable
    owner: str
    counterparty: Optional[str] = None
    direction: Direction
    current_deadline: Optional[datetime] = None
    status: RiskStatus
    status_reason: str                  # one-liner: why this status
    version_history: list[CommitmentVersion] = Field(default_factory=list)
    latest_source_ref: str = ""


# ── Layer 4: Briefing (output of daily briefing generator) ───

class BriefingSection(BaseModel):
    heading: str                        # "Overdue", "Due Today", etc.
    items: list[ReconciledCommitment]


class DailyBriefing(BaseModel):
    sim_date: datetime
    sections: list[BriefingSection]
    unowned_alerts: list[ReconciledCommitment] = Field(default_factory=list)