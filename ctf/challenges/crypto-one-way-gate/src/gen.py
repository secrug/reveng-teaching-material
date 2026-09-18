#!/usr/bin/env python3
"""crypto/one-way-gate ("Brick Wall") — Hard/400.  ANTI-AUTOMATION (TM-B).

Targets the automated-solver threat model, not the LLM one. Two published
anti-symbolic-execution techniques, used deliberately:

  1. ONE-WAY OPAQUE PREDICATE. The flag is checked through a murmur-style
     avalanche (multiply / shift / xor chain). SMT solvers are notoriously bad at
     chains of 32-bit multiplications, so a naive `angr` explore() cannot invert
     it and stalls.
  2. PATH-EXPLOSION PREDICATE. A second pass over the input takes a
     data-dependent branch per byte (2^n paths for a naive explorer) and feeds a
     checksum that is itself verified. It is *not* dead code, so it can't be
     pruned, and it floods a state-space search.

But the challenge is EASY for a human who reads it, because of the structure:
the input is consumed in 2-BYTE CHUNKS and the hash is CHAINED
(h_i depends only on chunk_i and h_{i-1}). So you brute-force 65536 candidates
per chunk, left to right — microseconds — instead of attacking 2^(8n) at once.

That asymmetry IS the lesson: understanding collapses a problem that brute force
and automation cannot touch.

Emits src/one-way-gate.c ; --selftest validates build + solve.
"""
import argparse, sys
M32 = 0xFFFFFFFF
IV  = 0x1234ABCD
C1, C2, C3 = 0x85EBCA6B, 0xC2B2AE35, 0x7F4A7C15

def mix(c, h, i):
    x = (c ^ (h & 0xFFFF)) & 0xFFFF
    y = (x * C1) & M32
    y ^= (y >> 13)
    y = (y * C2) & M32
    y ^= (y >> 16)
    y = (y + h + (i * C3)) & M32
    return y

def build_table(fb):
    assert len(fb) % 2 == 0, "flag length must be even"
    h = IV; table = []
    for i in range(len(fb) // 2):
        c = fb[2*i] | (fb[2*i+1] << 8)
        v = mix(c, h, i)
        table.append(v); h = v
    return table

def path_acc(fb):
    """The path-explosion pass: one data-dependent branch per byte."""
    acc = 0
    for b in fb:
        if b & 1: acc = (acc + b * 3) & M32
        else:     acc = (acc ^ (b * 5)) & M32
    return acc

def solve(table):
    """Recover the flag: 65536 candidates per chunk, chained left to right."""
    h = IV; out = bytearray()
    for i, target in enumerate(table):
        hits = [c for c in range(0x10000) if mix(c, h, i) == target]
        assert len(hits) == 1, f"chunk {i}: expected 1 preimage, got {len(hits)}"
        c = hits[0]
        out += bytes([c & 0xFF, (c >> 8) & 0xFF])
        h = target
    return bytes(out)

def carr32(name, data):
    return f"static const uint32_t {name}[] = {{{','.join(hex(v) + 'u' for v in data)}}};\n"

C_TEMPLATE = r'''/* one-way-gate : AURA-7 hardened unlock (auto-generated) */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

%TABLE%
static const uint32_t IV = %IV%u;
static const uint32_t ACC_TARGET = %ACC%u;
#define NCHUNK (sizeof TABLE / sizeof TABLE[0])

static uint32_t mix(uint16_t c, uint32_t h, uint32_t i){
    uint32_t x = (uint32_t)(c ^ (uint16_t)(h & 0xFFFF));
    uint32_t y = x * %C1%u;
    y ^= y >> 13;
    y = y * %C2%u;
    y ^= y >> 16;
    y = y + h + i * %C3%u;
    return y;
}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    if(n != NCHUNK*2){puts("nope.");return 1;}

    /* gate 1: chained one-way avalanche, 2 bytes at a time */
    uint32_t h = IV;
    for(size_t i=0;i<NCHUNK;i++){
        uint16_t c = (uint16_t)(in[2*i] | ((uint16_t)in[2*i+1] << 8));
        uint32_t v = mix(c, h, (uint32_t)i);
        if(v != TABLE[i]){puts("nope.");return 1;}
        h = v;
    }
    /* gate 2: path-explosion checksum — one data-dependent branch per byte */
    uint32_t acc = 0;
    for(size_t i=0;i<n;i++){
        unsigned char b = in[i];
        if(b & 1) acc = acc + (uint32_t)b * 3u;
        else      acc = acc ^ ((uint32_t)b * 5u);
    }
    if(acc != ACC_TARGET){puts("nope.");return 1;}

    puts("Gate open. That input is the flag.");
    return 0;
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", default="AURA{symb0lic_execution_hits_a_wall}")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    fb = a.flag.encode()
    if len(fb) % 2:
        sys.stderr.write("[gen] flag length must be even\n"); sys.exit(1)
    table = build_table(fb)
    acc = path_acc(fb)

    if a.selftest:
        rec = solve(table)
        assert rec == fb, f"solver failed: {rec!r}"
        assert path_acc(rec) == acc, "checksum mismatch"
        # a mutation must break gate 1
        bad = bytearray(fb); bad[4] ^= 1
        assert build_table(bytes(bad)) != table, "mutation not detected"
        print(f"one-way-gate OK")
        print(f"  flag    = {a.flag}  (len {len(fb)}, {len(table)} chunks)")
        print(f"  acc     = {acc:#010x}")
        print(f"  table[0:3] = {[hex(t) for t in table[:3]]}")
        print(f"  solved  = {rec.decode()}")
        return

    c = (C_TEMPLATE
         .replace("%TABLE%", carr32("TABLE", table))
         .replace("%IV%", str(IV)).replace("%ACC%", str(acc))
         .replace("%C1%", str(C1)).replace("%C2%", str(C2)).replace("%C3%", str(C3)))
    sys.stdout.write(c)
    sys.stderr.write(f"[gen] flag={a.flag!r} chunks={len(table)} acc={acc:#010x}\n")

if __name__ == "__main__":
    main()
