#!/usr/bin/env bash
# Proves aura-license is solvable end-to-end. Run in CI + before deploy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py > /tmp/aura-license.c 2>/dev/null
gcc -O2 -s -o /tmp/aura-license /tmp/aura-license.c
python3 solution/solve.py --live /tmp/aura-license
echo "OK: aura-license solvable"
