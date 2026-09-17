"""Load all 5 email threads → NormalizedEvent list."""

from __future__ import annotations

from datetime import datetime
from typing import List

from src.schemas import NormalizedEvent, SourceType
from .base_loader import BaseLoader

# Map email → display name
EMAIL_TO_NAME = {
    "arjun.malhotra@veridian-corp.example": "Arjun Malhotra",
    "neha.kapoor@veridian-corp.example": "Neha Kapoor",
    "raghav.sethi@veridian-corp.example": "Raghav Sethi",
    "divya.rao@veridian-corp.example": "Divya Rao",
    "priya.nair@meridianlogistics.example": "Priya Nair",
    "facilities@veridian-corp.example": "Facilities",
    "All Staff": "All Staff",
}


def _name(addr: str) -> str:
    return EMAIL_TO_NAME.get(addr, addr)


class EmailLoader(BaseLoader):
    THREAD_FILES = [
        "emails/thread_vendor_list.json",
        "emails/thread_deck_review.json",
        "emails/thread_meridian_call.json",
        "emails/thread_expense_report.json",
        "emails/thread_mumbai_lease.json",
    ]

    def load(self) -> List[NormalizedEvent]:
        events: List[NormalizedEvent] = []

        for rel_path in self.THREAD_FILES:
            raw = self._read_json(rel_path)
            thread_id = raw["thread_id"]
            subject = raw["subject"]

            for msg in raw["messages"]:
                ts = datetime.fromisoformat(msg["timestamp"])
                sender_email = msg["from"]
                recipients = [_name(r) for r in msg.get("to", [])]

                events.append(
                    NormalizedEvent(
                        source_type=SourceType.EMAIL,
                        timestamp=ts,
                        sender=_name(sender_email),
                        recipients=recipients,
                        subject=subject,
                        content=msg["body"],
                        source_ref=f"email:{thread_id}:msg_{msg['msg_id']}",
                        thread_id=thread_id,
                    )
                )

        return events