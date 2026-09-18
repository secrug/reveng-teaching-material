#!/usr/bin/env python3
"""Reference solver / healthcheck for padded-struct.
Recovers the flag by parsing the STEPS array with its REAL 8-byte stride
(op at +0, u32 k at +4 after 3 padding bytes) and inverting the per-byte op.
The whole point: read the stride correctly. A packed-5-byte assumption fails."""
import argparse, subprocess, sys, struct
MASK = 0xFF
# STEPS as they appear in .rodata: 8-byte stride, op@+0, k(u32 LE)@+4
STEPS_RODATA = bytes([0x00,0,0,0]) + struct.pack("<I",0x5A) \
             + bytes([0x03,0,0,0]) + struct.pack("<I",0x03) \
             + bytes([0x01,0,0,0]) + struct.pack("<I",0xB7) \
             + bytes([0x02,0,0,0]) + struct.pack("<I",0x29)
def parse_steps(rod):
    steps = []
    for off in range(0, len(rod), 8):                 # stride 8, NOT 5
        op = rod[off]
        k = struct.unpack_from("<I", rod, off + 4)[0]  # k at +4 after padding
        steps.append((op, k & 0xFF))
    return steps
STEPS = parse_steps(STEPS_RODATA); NS = len(STEPS)
def ror8(v,n): n&=7; return ((v>>n)|(v<<(8-n)))&MASK
def invert(t, i):
    op, k = STEPS[i % NS]
    if op == 0: return t ^ k
    if op == 1: return (t - k) & MASK
    if op == 2: return (t + k) & MASK
    if op == 3: return ror8(t, k)
DEFAULT_EXPECTED = bytes.fromhex(
    "1baa09182183eb3b3e4b253e054b2a362d431c493ffa2b3f3ffa24463e2b23362963204729eb")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected"); ap.add_argument("--live")
    a = ap.parse_args()
    exp = bytes.fromhex(a.expected) if a.expected else DEFAULT_EXPECTED
    flag = bytes(invert(exp[i], i) for i in range(len(exp)))
    print(flag.decode(errors="replace"))
    if a.live:
        r = subprocess.run([a.live], input=flag + b"\n", capture_output=True)
        ok = r.returncode == 0 and b"valid" in r.stdout.lower()
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
