#!/bin/sh
# Thin wrapper: macOS / Linux. Usage: ./install.sh [--dry-run] [--hooks] [--rollback]
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Python 3.8+ is required (https://www.python.org/downloads/)"; exit 1; }
exec "$PY" install.py "$@"
