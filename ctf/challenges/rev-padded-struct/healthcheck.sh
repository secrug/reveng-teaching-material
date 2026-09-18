#!/usr/bin/env bash
# Proves padded-struct is solvable end-to-end (default flag). Run in CI + before deploy.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py > /tmp/padded-struct.c 2>/dev/null
gcc -O2 -s -o /tmp/padded-struct /tmp/padded-struct.c
python3 solution/solve.py --live /tmp/padded-struct
echo "OK: padded-struct solvable"
