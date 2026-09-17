"""
Global configuration for the AIONOS Executive Agent.
Supports Groq (free), Anthropic, or Zero-Key Local Fallback.
"""

from pathlib import Path
from datetime import datetime, timezone
import os

# ── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROJECT_ROOT / "data" / "agent.db"

# ── Simulated clock ───────────────────────────────────────────
SIM_DATE_STR = os.environ.get("SIM_DATE", "2026-09-21 09:00")
SIM_NOW = datetime.strptime(SIM_DATE_STR, "%Y-%m-%d %H:%M").replace(
    tzinfo=timezone.utc
)

# ── LLM Configuration (Free API Support) ──────────────────────
# Options for keys: GROQ_API_KEY (free at console.groq.com), ANTHROPIC_API_KEY, or None
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Default free model on Groq: llama-3.3-70b-versatile
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# ── Risk thresholds ───────────────────────────────────────────
HOURS_TO_DEADLINE_AT_RISK = 24
HOURS_SILENCE_STALLED = 4