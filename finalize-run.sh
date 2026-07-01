#!/usr/bin/env bash
# Default post-run pipeline: salvage → update-candidates → per-run findings → mark saved.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/lib/finalize-run.py" "$@"
