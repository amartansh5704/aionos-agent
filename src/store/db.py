"""
SQLite Storage Layer for Normalized Events and Reconciled Commitments.
"""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from config import DB_PATH
from src.schemas import NormalizedEvent, ReconciledCommitment


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS normalized_events (
                    source_ref TEXT PRIMARY KEY,
                    source_type TEXT,
                    timestamp TEXT,
                    sender TEXT,
                    recipients TEXT,
                    subject TEXT,
                    content TEXT,
                    thread_id TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reconciled_commitments (
                    task_id TEXT PRIMARY KEY,
                    task_label TEXT,
                    owner TEXT,
                    counterparty TEXT,
                    direction TEXT,
                    current_deadline TEXT,
                    status TEXT,
                    status_reason TEXT,
                    version_history TEXT,
                    latest_source_ref TEXT
                )
                """
            )
            conn.commit()

    def save_events(self, events: List[NormalizedEvent]):
        with self._get_conn() as conn:
            for e in events:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO normalized_events
                    (source_ref, source_type, timestamp, sender, recipients, subject, content, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        e.source_ref,
                        e.source_type.value,
                        e.timestamp.isoformat(),
                        e.sender,
                        json.dumps(e.recipients),
                        e.subject,
                        e.content,
                        e.thread_id,
                    ),
                )
            conn.commit()

    def save_reconciled(self, commitments: List[ReconciledCommitment]):
        with self._get_conn() as conn:
            for c in commitments:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO reconciled_commitments
                    (task_id, task_label, owner, counterparty, direction, current_deadline, status, status_reason, version_history, latest_source_ref)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c.task_id,
                        c.task_label,
                        c.owner,
                        c.counterparty,
                        c.direction.value,
                        c.current_deadline.isoformat() if c.current_deadline else None,
                        c.status.value,
                        c.status_reason,
                        json.dumps([v.model_dump(mode="json") for v in c.version_history]),
                        c.latest_source_ref,
                    ),
                )
            conn.commit()

    def get_events(self) -> List[NormalizedEvent]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM normalized_events ORDER BY timestamp").fetchall()
            events = []
            for r in rows:
                events.append(
                    NormalizedEvent(
                        source_type=r["source_type"],
                        timestamp=r["timestamp"],
                        sender=r["sender"],
                        recipients=json.loads(r["recipients"]),
                        subject=r["subject"],
                        content=r["content"],
                        source_ref=r["source_ref"],
                        thread_id=r["thread_id"],
                    )
                )
            return events

    def get_reconciled(self) -> List[ReconciledCommitment]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM reconciled_commitments").fetchall()
            reconciled = []
            for r in rows:
                vh_data = json.loads(r["version_history"])
                reconciled.append(
                    ReconciledCommitment(
                        task_id=r["task_id"],
                        task_label=r["task_label"],
                        owner=r["owner"],
                        counterparty=r["counterparty"],
                        direction=r["direction"],
                        current_deadline=r["current_deadline"],
                        status=r["status"],
                        status_reason=r["status_reason"],
                        version_history=vh_data,
                        latest_source_ref=r["latest_source_ref"],
                    )
                )
            return reconciled