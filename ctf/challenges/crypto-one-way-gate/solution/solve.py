#!/usr/bin/env python3
"""Reference solver / healthcheck for one-way-gate.

The insight: the avalanche is CHAINED over 2-BYTE CHUNKS, so chunk i depends only
on chunk i and h_{i-1}. Brute-force 65536 candidates per chunk, left to right —
about a million operations total — instead of attacking the whole input at once.

This is why a symbolic solver stalls and a human does not: angr sees one giant
non-linear constraint over 36 symbolic bytes (plus 2^36 paths from the checksum
loop); we see 18 independent 16-bit searches.
"""
import argparse, subprocess, sys
M32 = 0xFFFFFFFF
IV  = 0x1234ABCD
C1, C2, C3 = 0x85EBCA6B, 0xC2B2AE35, 0x7F4A7C15    # read off the disassembly

def mix(c, h, i):
    x = (c ^ (h & 0xFFFF)) & 0xFFFF
    y = (x * C1) & M32
    y ^= (y >> 13)
    y = (y * C2) & M32
    y ^= (y >> 16)
    return (y + h + (i * C3)) & M32

DEFAULT_TABLE = [0x32775a35,0x29fed997,0x8a551fbd,0xb10184d0,0x91fe9bf2,0x10e3a7bd,
                 0x42852e78,0xf25b74c7,0xaa936662,0x6d1572aa,0x7892f00f,0xab920360,
                 0x44f81b15,0x1c6ecd3a,0x65938384,0xc890a016,0xdb60f649,0x90f4f026]

def solve(table):
    h = IV; out = bytearray()
    for i, target in enumerate(table):
        for c in range(0x10000):                  # 16-bit search, chained
            if mix(c, h, i) == target:
                out += bytes([c & 0xFF, (c >> 8) & 0xFF]); h = target
                break
        else:
            raise SystemExit(f"no preimage for chunk {i}")
    return bytes(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", help="comma-separated hex u32 TABLE dumped from the binary")
    ap.add_argument("--live", help="path to built binary; verify the recovered flag")
    a = ap.parse_args()
    table = [int(x, 16) for x in a.table.split(",")] if a.table else DEFAULT_TABLE
    flag = solve(table)
    print(flag.decode(errors="replace"))
    if a.live:
        r = subprocess.run([a.live], input=flag + b"\n", capture_output=True)
        ok = r.returncode == 0 and b"gate open" in r.stdout.lower()
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
