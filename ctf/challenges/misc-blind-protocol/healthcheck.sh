#!/usr/bin/env bash
# Proves the service is up, solvable, AND still trap-hardened.
# Usage: ./healthcheck.sh [host] [port]
set -euo pipefail
cd "$(dirname "$0")"
HOST="${1:-127.0.0.1}"; PORT="${2:-9007}"
python3 src/make_pcap.py --verify                       # capture still coherent
python3 src/verify_trap.py "$HOST" "$PORT"              # replay + naive XOR must fail
python3 solution/solve.py --host "$HOST" --port "$PORT" --live
echo "OK: blind-protocol solvable and trap intact"
