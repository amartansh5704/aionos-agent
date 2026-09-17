"""
Pipeline script: Ingests raw data -> extracts commitments -> reconciles -> saves to SQLite DB.
"""

import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timezone
from config import SIM_NOW
from src.ingestion import load_all_raw
from src.extraction.commitment_extractor import CommitmentExtractor
from src.reconciliation import ReconciliationEngine
from src.store.db import Database


def run_pipeline(sim_now: datetime = SIM_NOW):
    print(f"--- Running Pipeline for Simulated Date: {sim_now.isoformat()} ---")

    # 1. Ingestion
    events = load_all_raw()
    print(f"[1/4] Ingested {len(events)} events.")

    # 2. Extraction
    extractor = CommitmentExtractor()
    commitments = extractor.extract_all(events)
    print(f"[2/4] Extracted {len(commitments)} commitments.")

    # 3. Reconciliation
    reconciler = ReconciliationEngine()
    reconciled = reconciler.reconcile(commitments, events, sim_now)
    print(f"[3/4] Reconciled into {len(reconciled)} unique tasks.")

    # 4. Storage
    db = Database()
    db.save_events(events)
    db.save_reconciled(reconciled)
    print(f"[4/4] Saved state to SQLite DB ({db.db_path}).")


if __name__ == "__main__":
    run_pipeline()