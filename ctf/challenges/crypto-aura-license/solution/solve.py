#!/usr/bin/env python3
"""Reference keygen / healthcheck for aura-license (ALC-64).

Reimplements the cipher recovered from the binary and ENCRYPTS the magic
plaintext to produce the single licence the validator accepts.

Everything below is dumped or read off the disassembly — nothing is assumed:
  SBOX  : 256 bytes from .rodata
  KEY   : 8 bytes from .rodata (per-instance)
  MAGIC : 8 bytes from .rodata ("AURA-LIC")
  F, schedule, round count : read from the code
"""
import argparse, subprocess, sys
M32 = 0xFFFFFFFF; M64 = 0xFFFFFFFFFFFFFFFF
ROUNDS = 16
LCG_A, LCG_C = 6364136223846793005, 1442695040888963407   # from the schedule routine

SBOX = bytes.fromhex(
 "e68d701619d8c272d35251451007aa41506c4a6e050b2fa5fd979f6fa344b7be"
 "ee17cbbf1a695a89e3afea2594bd765bf26da11d5f276029ef12fbd29990ba3c"
 "088b3d79adbc2a88939bf533d75811d5817c663a221492ed1cdb98acc52e4d40"
 "c106bbe2b965f4ccfff8682c04a49efa7834ab37847a0996b5a84f5c7d9d4e8f"
 "61d6468302e1954c86b00ae4b20c28b3f1ecf0534b910143c8f30f3fc3d1368c"
 "f7b1e90323f971e8e780d08e6749188aa9ae823e8531b4873832561ec6a05dfe"
 "a6246b5564dcd4547ecacf773b74b8262d0073e5d921da7bfc0e48ce6ac7c959"
 "c06330472bcd13f61f759a204239a77f1be015deb60ddd3557c4ebdf9c5e62a2")
DEFAULT_KEY = bytes.fromhex("0f1e2d3c4b5a6978")
MAGIC = b"AURA-LIC"

def rotl32(v, n): n &= 31; return ((v << n) | (v >> (32 - n))) & M32
def sbox_bytes(x):
    return ( SBOX[x & 0xFF] | (SBOX[(x >> 8) & 0xFF] << 8)
           | (SBOX[(x >> 16) & 0xFF] << 16) | (SBOX[(x >> 24) & 0xFF] << 24) ) & M32
def F(R, k):
    x = rotl32((R ^ k) & M32, 7)
    return (sbox_bytes(x) + rotl32(k, 11)) & M32
def key_schedule(master8):
    st = int.from_bytes(master8, "little") & M64; ks = []
    for _ in range(ROUNDS):
        st = (st * LCG_A + LCG_C) & M64
        ks.append((st >> 32) & M32)
    return ks
def encrypt(b8, ks):
    L = int.from_bytes(b8[0:4], "little"); R = int.from_bytes(b8[4:8], "little")
    for i in range(ROUNDS):
        L, R = R, (L ^ F(R, ks[i])) & M32
    return L.to_bytes(4, "little") + R.to_bytes(4, "little")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=DEFAULT_KEY.hex(), help="master key hex dumped from the binary")
    ap.add_argument("--live", help="path to built binary; verify the forged licence")
    a = ap.parse_args()
    ks = key_schedule(bytes.fromhex(a.key))
    lic = encrypt(MAGIC, ks)                    # the ONE licence that decrypts to MAGIC
    flag = "AURA{" + lic.hex() + "}"
    print(f"licence: {lic.hex()}")
    print(flag)
    if a.live:
        r = subprocess.run([a.live], input=lic.hex().encode() + b"\n", capture_output=True)
        ok = r.returncode == 0 and flag.encode() in r.stdout
        print(f"[healthcheck] {'ACCEPTED' if ok else 'REJECTED'}: {r.stdout!r}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
