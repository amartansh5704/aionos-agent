#!/usr/bin/env bash
set -e

echo "=================================================="
echo "AIONOS Executive Productivity Agent Launcher"
echo "=================================================="

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 10)" || { echo "Python 3.10+ required"; exit 1; }

# Install requirements if needed
pip install -q -r requirements.txt

# Run database seed
python scripts/seed_db.py

# Launch web server
python web/app.py