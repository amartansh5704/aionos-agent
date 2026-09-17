"""Load Arjun's personal voice memos → NormalizedEvent list."""

from __future__ import annotations

from datetime import datetime
from typing import List

from src.schemas import NormalizedEvent, SourceType
from .base_loader import BaseLoader


class VoiceNoteLoader(BaseLoader):
    NOTE_FILES = [
        "voice_notes/voice_note_1.json",
        "voice_notes/voice_note_2.json",
    ]

    def load(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        for rel_path in self.NOTE_FILES:
            raw = self._read_json(rel_path)
            ts = datetime.fromisoformat(raw["timestamp"])
            note_id = raw["note_id"]

            events.append(
                NormalizedEvent(
                    source_type=SourceType.VOICE_NOTE,
                    timestamp=ts,
                    sender=raw["recorded_by"],  # Arjun Malhotra
                    recipients=[],  # self-memo, no recipients
                    subject=f"Voice memo ({raw.get('context', 'personal')})",
                    content=raw["transcript"],
                    source_ref=f"voice_note:{note_id}",
                    thread_id=note_id,
                )
            )

        return events