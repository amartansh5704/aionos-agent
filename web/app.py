"""
Flask Web Application & API Endpoint Layer.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timezone
from flask import Flask, jsonify, request

from src.ingestion import load_all_raw
from src.extraction.commitment_extractor import CommitmentExtractor
from src.reconciliation import ReconciliationEngine
from src.briefing.daily_briefing import DailyBriefingGenerator
from src.query.query_engine import QueryEngine

# Explicit paths for Vercel deployment
static_path = str(ROOT_DIR / "web" / "static")
app = Flask(__name__, static_folder=static_path, static_url_path="/static")

# In-memory pipeline cache
RAW_EVENTS = load_all_raw()
EXTRACTOR = CommitmentExtractor()
EXTRACTED_COMMITMENTS = EXTRACTOR.extract_all(RAW_EVENTS)
RECONCILER = ReconciliationEngine()
BRIEFING_GEN = DailyBriefingGenerator()


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/briefing", methods=["GET"])
def get_briefing():
    sim_date_str = request.args.get("sim_date", "2026-09-21 09:00")
    try:
        sim_now = datetime.strptime(sim_date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        sim_now = datetime(2026, 9, 21, 9, 0, tzinfo=timezone.utc)

    reconciled = RECONCILER.reconcile(EXTRACTED_COMMITMENTS, RAW_EVENTS, sim_now)
    briefing = BRIEFING_GEN.generate_briefing(sim_now, reconciled)

    return jsonify(briefing.model_dump(mode="json"))


@app.route("/api/query", methods=["POST"])
def query_agent():
    data = request.json or {}
    user_query = data.get("query", "")
    sim_date_str = data.get("sim_date", "2026-09-21 09:00")

    try:
        sim_now = datetime.strptime(sim_date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        sim_now = datetime(2026, 9, 21, 9, 0, tzinfo=timezone.utc)

    reconciled = RECONCILER.reconcile(EXTRACTED_COMMITMENTS, RAW_EVENTS, sim_now)
    q_engine = QueryEngine(reconciled, RAW_EVENTS)
    result = q_engine.answer_query(user_query, sim_now)

    return jsonify(result)


# Vercel entrypoint handler
app_handler = app

if __name__ == "__main__":
    print("\n🚀 Starting AIONOS Executive Productivity Agent Server...")
    print("👉 Open http://127.0.0.1:5000 in your browser\n")
    app.run(host="0.0.0.0", port=5000, debug=True)