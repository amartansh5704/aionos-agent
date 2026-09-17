"""
Validates the 5 test scenarios from §9 of the PRD.
"""

from datetime import datetime, timezone
import pytest

from src.ingestion import load_all_raw
from src.extraction.commitment_extractor import CommitmentExtractor
from src.reconciliation import ReconciliationEngine
from src.schemas import RiskStatus


@pytest.fixture(scope="module")
def extracted_data():
    events = load_all_raw()
    extractor = CommitmentExtractor()
    commitments = extractor.extract_all(events)
    return events, commitments


# Scenario 1: Wed 23 Sept, 9:00 AM -> Vendor list should be STALLED
def test_scenario_1_vendor_list_stalled(extracted_data):
    events, commitments = extracted_data
    sim_now = datetime(2026, 9, 23, 9, 0, tzinfo=timezone.utc)

    engine = ReconciliationEngine()
    reconciled = engine.reconcile(commitments, events, sim_now)

    vendor_item = next(r for r in reconciled if r.task_id == "vendor_list")
    assert vendor_item.status == RiskStatus.STALLED
    assert "Unanswered follow-up" in vendor_item.status_reason or "Raghav" in vendor_item.status_reason


# Scenario 2: Thu 24 Sept, 9:00 AM -> Deck review should be ON_TRACK or CLOSED
def test_scenario_2_deck_review_on_track(extracted_data):
    events, commitments = extracted_data
    sim_now = datetime(2026, 9, 24, 9, 0, tzinfo=timezone.utc)

    engine = ReconciliationEngine()
    reconciled = engine.reconcile(commitments, events, sim_now)

    deck_item = next(r for r in reconciled if r.task_id == "deck_review")
    assert deck_item.status in [RiskStatus.ON_TRACK, RiskStatus.CLOSED]


# Scenario 3: Wed 23 Sept, 6:15 PM -> Expense report should be CLOSED
def test_scenario_3_expense_report_closed(extracted_data):
    events, commitments = extracted_data
    sim_now = datetime(2026, 9, 23, 18, 15, tzinfo=timezone.utc)

    engine = ReconciliationEngine()
    reconciled = engine.reconcile(commitments, events, sim_now)

    expense_item = next(r for r in reconciled if r.task_id == "expense_report")
    assert expense_item.status == RiskStatus.CLOSED


# Scenario 4: Thu 24 Sept, 5:00 PM -> Mumbai lease should be UNOWNED
def test_scenario_4_mumbai_lease_unowned(extracted_data):
    events, commitments = extracted_data
    sim_now = datetime(2026, 9, 24, 17, 0, tzinfo=timezone.utc)

    engine = ReconciliationEngine()
    reconciled = engine.reconcile(commitments, events, sim_now)

    lease_item = next(r for r in reconciled if r.task_id == "mumbai_lease")
    assert lease_item.status == RiskStatus.UNOWNED


# Scenario 5: Wed 23 Sept, 3:30 PM -> Meridian call should be CLOSED
def test_scenario_5_meridian_call_closed(extracted_data):
    events, commitments = extracted_data
    sim_now = datetime(2026, 9, 23, 15, 30, tzinfo=timezone.utc)

    engine = ReconciliationEngine()
    reconciled = engine.reconcile(commitments, events, sim_now)

    meridian_item = next(r for r in reconciled if r.task_id == "meridian_call")
    assert meridian_item.status == RiskStatus.CLOSED