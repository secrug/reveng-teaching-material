#!/usr/bin/env python3
"""Reference solver / healthcheck for warmup-decoder.
Recovers the flag from expected[] and the visible KEY. Method is per-instance:
dump this instance's expected[] and re-run. (This is the AI-friendly challenge;
a model one-shots it. That is the intended lesson.)"""
import argparse, subprocess, sys
MASK = 0xFF
KEY = b"AURA-SIGNAL-KEY"                       # printed by `strings`
def ror8(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & MASK
def invert(t, i): return ror8(t ^ KEY[i % len(KEY)], 3)
DEFAULT_EXPECTED = bytes.fromhex(
    "4bffc04bf6e8e8d425eacfd7e80672bb3e595a6e183a6cb40ad7d7703e2262af59e2d7f00a0cd5aa")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected"); ap.add_argument("--live")
    a = ap.parse_args()
    exp = bytes.fromhex(a.expected) if a.expected else DEFAULT_EXPECTED
    flag = bytes(invert(exp[i], i) for i in range(len(exp)))
    print(flag.decode(errors="replace"))
    if a.live:
        r = subprocess.run([a.live], input=flag + b"\n", capture_output=True)
        ok = r.returncode == 0 and b"accepted" in r.stdout.lower()
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
