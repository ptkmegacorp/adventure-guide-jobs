#!/usr/bin/env bash
# Deterministically extract final LiteResearcher answer to runs/extracted/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/lib/extract-findings.py" "$@"
