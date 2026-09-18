#!/usr/bin/env bash
# Proves one-way-gate is solvable end-to-end. Run in CI + before deploy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py > /tmp/one-way-gate.c 2>/dev/null
gcc -O2 -s -o /tmp/one-way-gate /tmp/one-way-gate.c
python3 solution/solve.py --live /tmp/one-way-gate
echo "OK: one-way-gate solvable"
