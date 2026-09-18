#!/usr/bin/env bash
# Build the binary and prove the reference exploit lands the flag.
# REQUIRES a Linux host with gcc + python3 + pwntools. This is the
# verify-on-build gate (cannot run on the Windows authoring box).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
gcc -O0 -fno-stack-protector -no-pie -o "$tmp/telemetry-heap" "$here/src/telemetry-heap.c"
echo 'AURA{healthcheck_local}' > "$tmp/flag.txt"
cp "$here/solution/exploit.py" "$tmp/exploit.py"
( cd "$tmp" && python3 exploit.py ) | grep -q 'AURA{healthcheck_local}'   && echo "OK: telemetry-heap exploit lands the flag"   || { echo "FAIL: telemetry-heap exploit did not recover the flag"; exit 1; }
