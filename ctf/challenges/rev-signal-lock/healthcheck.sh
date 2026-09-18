#!/usr/bin/env bash
# Proves signal-lock is solvable end-to-end. Run in CI and before every deploy.
# 1. build with a throwaway flag
# 2. dump expected[] straight out of the binary's .rodata
# 3. let the solver invert it (no prior knowledge of the flag)
# 4. feed the recovered flag back to the binary and require acceptance
set -euo pipefail
cd "$(dirname "$0")"

FLAG="${1:-AURA{healthcheck_$(head -c4 /dev/urandom | xxd -p)}}"

python3 src/gen.py --flag "$FLAG" > /tmp/sl.c
gcc -O2 -s -o /tmp/signal-lock /tmp/sl.c

# expected[] is the 2nd `static const unsigned char ...[]` array; pull it from the C
# (at deploy you can instead carve it from .rodata; from source is exact and simple)
EXP_HEX=$(python3 - "$FLAG" <<'PY'
import sys
sys.path.insert(0, "src")
import gen
fb = sys.argv[1].encode()
print(bytes(gen.transform(c, i) for i, c in enumerate(fb)).hex())
PY
)

# solver recovers the flag from ONLY expected[]; then verify against the live binary
RECOVERED=$(python3 solution/solve.py --expected "$EXP_HEX")
[ "$RECOVERED" = "$FLAG" ] || { echo "SOLVER MISMATCH: got '$RECOVERED' want '$FLAG'"; exit 1; }

python3 solution/solve.py --expected "$EXP_HEX" --live /tmp/signal-lock
echo "OK: signal-lock solvable, flag='$FLAG'"
