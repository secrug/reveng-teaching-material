#!/usr/bin/env bash
# Regenerates the image and proves it parses + yields the real (not decoy) flag.
set -euo pipefail
cd "$(dirname "$0")"
python3 src/gen.py --selftest
python3 src/gen.py -o /tmp/aura-fw.bin
python3 solution/solve.py /tmp/aura-fw.bin --live
echo "OK: firmware-triage solvable"
