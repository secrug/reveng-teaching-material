#!/usr/bin/env bash
# Proves mirror is solvable end-to-end (default flag). Run in CI + before deploy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py > /tmp/mirror.c 2>/dev/null
gcc -O2 -s -o /tmp/mirror /tmp/mirror.c
python3 solution/solve.py --live /tmp/mirror
echo "OK: mirror solvable"
