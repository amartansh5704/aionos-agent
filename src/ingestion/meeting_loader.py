"""Load Leadership Sync meeting transcript → NormalizedEvent list."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from src.schemas import NormalizedEvent, SourceType
from .base_loader import BaseLoader


class MeetingLoader(BaseLoader):
    def load(self) -> List[NormalizedEvent]:
        raw = self._read_json("meeting_transcript.json")

        # Meeting start as base timestamp
        date_str = raw["date"]  # "2026-09-21"
        start = raw["start_time"]  # "09:00"
        base_ts = datetime.fromisoformat(f"{date_str}T{start}:00").replace(
            tzinfo=timezone.utc
        )

        attendees = raw.get("attendees", [])
        events: List[NormalizedEvent] = []

        for i, turn in enumerate(raw["transcript"]):
            # Stagger turns by ~30s so ordering is stable
            ts = base_ts.replace(second=min(i * 30, 59))
            speaker = turn["speaker"]
            text = turn["text"]

            events.append(
                NormalizedEvent(
                    source_type=SourceType.MEETING,
                    timestamp=ts,
                    sender=speaker,
                    recipients=[a for a in attendees if a != speaker],
                    subject=raw.get("title", "Leadership Sync"),
                    content=f"{speaker}: {text}",
                    source_ref=f"meeting:leadership_sync:turn_{i+1}",
                    thread_id="meeting_leadership_sync",
                )
            )

        return events