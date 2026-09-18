#!/usr/bin/env python3
"""Reference solver / healthcheck for asp-coprocessor.
Once the loop's per-byte transform is recovered from the ASP program
  t = ( rol8(c ^ K1, i&7) + (K2 + i*K4) ) & 0xFF ^ K3
invert it byte-by-byte over expected[]. Method is per-instance: dump this
instance's expected[] and re-run."""
import argparse, subprocess, sys
MASK=0xFF
K1,K2,K3,K4 = 0x5A,0x1B,0x3C,0x11             # recovered from the MOVI immediates
def ror8(v,n): n&=7; return ((v>>n)|(v<<(8-n)))&MASK
def invert(t,i):
    u = t ^ K3
    u = (u - (K2 + i*K4)) & MASK
    u = ror8(u, i&7)
    return u ^ K1
DEFAULT_EXPECTED = bytes.fromhex(
    "0a76611a4debfe95f716a923b5a22f0d0ca4d1cb7e1b5c8ace7cd5aba1699f90541e29c3f3ab9773cb7a91d3a5c0")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expected"); ap.add_argument("--live")
    a=ap.parse_args()
    exp=bytes.fromhex(a.expected) if a.expected else DEFAULT_EXPECTED
    flag=bytes(invert(exp[i], i) for i in range(len(exp)))
    print(flag.decode(errors="replace"))
    if a.live:
        r=subprocess.run([a.live], input=flag+b"\n", capture_output=True)
        ok=r.returncode==0 and b"unlocked" in r.stdout.lower()
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__=="__main__":
    main()
