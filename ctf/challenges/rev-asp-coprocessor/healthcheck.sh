#!/usr/bin/env bash
# Proves asp-coprocessor is solvable end-to-end (default flag). Run in CI + before deploy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py > /tmp/asp-coprocessor.c 2>/dev/null
gcc -O2 -s -o /tmp/asp-coprocessor /tmp/asp-coprocessor.c
python3 solution/solve.py --live /tmp/asp-coprocessor
echo "OK: asp-coprocessor solvable"
