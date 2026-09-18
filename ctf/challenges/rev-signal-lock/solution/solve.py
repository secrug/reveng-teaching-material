#!/usr/bin/env python3
"""Reference solver + healthcheck for `signal-lock`.

Two modes:
  * default        : recover the flag by inverting the observed transform.
  * --live PATH    : run the built binary, feed it the recovered flag, and
                     assert it accepts (used by healthcheck.sh / CI).

The solver embeds ONLY what a player recovers from the binary by hand:
  - the per-byte transform (deduced from the ASP program), and
  - the expected[] table (read out of .rodata / observed at the CHECK port).
It does NOT know the flag in advance; it derives it. That is the whole point:
the solution is a method, so it works for any per-instance expected[] table.
"""
import argparse, subprocess, sys

MASK = 0xFF
K1, K2, K3 = 0x5A, 0x1B, 0x3C          # recovered from the MOVI immediates in the program

def ror8(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & MASK

def invert(t, i):
    u = t ^ K3
    u = (u - (i * K2)) & MASK
    u = ror8(u, i & 7)
    return u ^ K1

def recover(expected: bytes) -> bytes:
    return bytes(invert(expected[i], i) for i in range(len(expected)))

# expected[] as read out of the reference binary's .rodata (per-instance: re-dump)
DEFAULT_EXPECTED = bytes.fromhex("27056a1542701166e179872ebbfa3b2bdaa3f6b6b2")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", help="hex of expected[] dumped from the binary")
    ap.add_argument("--live", help="path to built binary; verify recovered flag is accepted")
    a = ap.parse_args()

    expected = bytes.fromhex(a.expected) if a.expected else DEFAULT_EXPECTED
    flag = recover(expected)
    print(flag.decode(errors="replace"))

    if a.live:
        out = subprocess.run([a.live], input=flag + b"\n", capture_output=True)
        ok = out.returncode == 0 and b"unlocked" in out.stdout.lower()
        print(f"[healthcheck] binary {'ACCEPTED' if ok else 'REJECTED'} the recovered flag",
              file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
