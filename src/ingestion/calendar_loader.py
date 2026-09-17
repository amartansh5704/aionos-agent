"""Load all personal calendars → NormalizedEvent list."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from src.schemas import NormalizedEvent, SourceType
from .base_loader import BaseLoader


class CalendarLoader(BaseLoader):
    CALENDAR_FILES = [
        "calendars/arjun.json",
        "calendars/neha.json",
        "calendars/raghav.json",
        "calendars/divya.json",
    ]

    def load(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        for rel_path in self.CALENDAR_FILES:
            full = self.raw_dir / rel_path
            if not full.exists():
                print(f"[calendar] skip missing {rel_path}")
                continue

            raw = self._read_json(rel_path)
            person = raw["person"]
            slug = Path(rel_path).stem  # arjun, neha, ...

            for i, ev in enumerate(raw.get("events", [])):
                start_ts = datetime.fromisoformat(
                    f"{ev['date']}T{ev['start']}:00"
                ).replace(tzinfo=timezone.utc)
                end_ts = datetime.fromisoformat(
                    f"{ev['date']}T{ev['end']}:00"
                ).replace(tzinfo=timezone.utc)

                content = (
                    f"Calendar event for {person}: {ev['title']} "
                    f"({ev['start']}–{ev['end']} on {ev['date']})"
                )

                events.append(
                    NormalizedEvent(
                        source_type=SourceType.CALENDAR,
                        timestamp=start_ts,
                        sender=person,
                        recipients=[],
                        subject=ev["title"],
                        content=content,
                        source_ref=f"calendar:{slug}:event_{i+1}",
                        thread_id=f"calendar_{slug}",
                    )
                )
                # attach end time in content only; schema stays flat

        return events