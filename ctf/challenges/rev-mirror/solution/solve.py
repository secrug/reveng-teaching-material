#!/usr/bin/env python3
"""Reference solver / healthcheck for mirror.
The keystream is NOT stored in the clear: KS[i] = CT[i] ^ lcg8(i). Reimplement
the LCG (recovered from the disassembly, or dumped by running the binary), then
invert. Static extraction of CT[]/expected[] yields noise without the LCG."""
import argparse, subprocess, sys
MASK=0xFF; MASK32=0xFFFFFFFF
A, C, SEED = 1103515245, 12345, 0x63          # recovered from the PRNG loop
def ror8(v,n): n%=8; return ((v>>n)|(v<<(8-n)))&MASK
def keystream(n):
    s=SEED; out=[]
    for _ in range(n):
        s=(s*A+C)&MASK32; out.append((s>>8)&0xFF)
    return out
def recover(CT, expected):
    n=len(expected); kb=keystream(n)
    KS=[CT[i]^kb[i] for i in range(n)]
    return bytes(ror8(expected[i]^KS[i], i%7) for i in range(n))
DEFAULT_CT=bytes.fromhex("0b30557a9fc4e90e33587da2c7ec11365b80a5caef14395e83a8cdf2173c6186abd0f51a")
DEFAULT_EXP=bytes.fromhex("ce573d4fae0b8e22a4233833728d83341b8dee719961d00d96783244e388c1794ed6ceee")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ct"); ap.add_argument("--expected"); ap.add_argument("--live")
    a=ap.parse_args()
    CT=bytes.fromhex(a.ct) if a.ct else DEFAULT_CT
    exp=bytes.fromhex(a.expected) if a.expected else DEFAULT_EXP
    flag=recover(list(CT), list(exp))
    print(flag.decode(errors="replace"))
    if a.live:
        r=subprocess.run([a.live], input=flag+b"\n", capture_output=True)
        ok=r.returncode==0 and b"matched" in r.stdout.lower()
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__=="__main__":
    main()
