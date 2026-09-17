"""
Abstract base loader + orchestrator. Concrete loaders subclass
BaseLoader and implement `load() -> list[NormalizedEvent]`.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from src.schemas import NormalizedEvent
from config import DATA_RAW, DATA_PROCESSED


class BaseLoader(ABC):
    def __init__(self, raw_dir: Path = DATA_RAW):
        self.raw_dir = raw_dir

    @abstractmethod
    def load(self) -> List[NormalizedEvent]:
        ...

    def _read_json(self, relative_path: str) -> dict | list:
        full = self.raw_dir / relative_path
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_text(self, relative_path: str) -> str:
        full = self.raw_dir / relative_path
        return full.read_text(encoding="utf-8")


def load_all_raw() -> List[NormalizedEvent]:
    events: List[NormalizedEvent] = []

    try:
        from .meeting_loader import MeetingLoader
        events.extend(MeetingLoader().load())
    except ImportError:
        pass

    try:
        from .calendar_loader import CalendarLoader
        events.extend(CalendarLoader().load())
    except ImportError:
        pass

    try:
        from .email_loader import EmailLoader
        events.extend(EmailLoader().load())
    except ImportError:
        pass

    try:
        from .voice_note_loader import VoiceNoteLoader
        events.extend(VoiceNoteLoader().load())
    except ImportError:
        pass

    events.sort(key=lambda e: e.timestamp)

    # Safe write (catches read-only environment error on Vercel gracefully)
    try:
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        out = DATA_PROCESSED / "normalized_events.json"
        out.write_text(
            json.dumps(
                [e.model_dump(mode="json") for e in events],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass  # Proceed in-memory on serverless platforms

    return events