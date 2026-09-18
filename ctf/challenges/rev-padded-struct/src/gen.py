#!/usr/bin/env python3
"""rev/padded-struct ("Wire Format") — Easy/150.

AI target: struct alignment padding (the S5 failure mode). The transform reads
per-position parameters from an array of

    struct step { uint8_t op; uint32_t k; };   // sizeof == 8 (3 pad bytes after op)

The compiler inserts 3 padding bytes after `op` so `k` is 4-byte aligned. A solver
(or model) that assumes a *packed* 5-byte layout reads `op`/`k` from the wrong
offsets and recovers garbage. You must parse the real 8-byte stride.

Per input byte i: s = STEPS[i % NS]; apply op with constant (s.k & 0xFF):
    op 0: xor   op 1: add   op 2: sub   op 3: rol
All invertible. Emits src/padded-struct.c ; --selftest verifies round-trip and
that the emitted .rodata really has the 8-byte stride with zero padding bytes.
"""
import argparse, struct, sys
MASK = 0xFF
# (op, k)  -- k used as (k & 0xFF); full u32 stored to make the stride obvious
STEPS = [(0, 0x0000005A), (3, 0x00000003), (1, 0x000000B7), (2, 0x00000029)]
NS = len(STEPS)
def rol8(v,n): n&=7; return ((v<<n)|(v>>(8-n)))&MASK
def ror8(v,n): n&=7; return ((v>>n)|(v<<(8-n)))&MASK

def apply_step(c, op, k):
    k &= 0xFF
    if op == 0: return c ^ k
    if op == 1: return (c + k) & MASK
    if op == 2: return (c - k) & MASK
    if op == 3: return rol8(c, k)
    raise ValueError
def invert_step(t, op, k):
    k &= 0xFF
    if op == 0: return t ^ k
    if op == 1: return (t - k) & MASK
    if op == 2: return (t + k) & MASK
    if op == 3: return ror8(t, k)
    raise ValueError
def transform(c, i): op,k = STEPS[i % NS]; return apply_step(c, op, k)
def invert(t, i):    op,k = STEPS[i % NS]; return invert_step(t, op, k)

def steps_rodata():
    """Bytes of `struct step STEPS[NS]` with real alignment: op, 3 pad, u32 k."""
    b = bytearray()
    for op, k in STEPS:
        b.append(op); b += b"\x00\x00\x00"; b += struct.pack("<I", k)
    return bytes(b)

def carr(name, data): return f"static const unsigned char {name}[] = {{{','.join(map(str,data))}}};\n"

C_TEMPLATE = r'''/* padded-struct : AURA-7 wire-format verifier (auto-generated) */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

/* The compiler pads this: sizeof(struct step)==8, k at offset 4, NOT 1. */
struct step { uint8_t op; uint32_t k; };
static const struct step STEPS[] = {
%STEPS_INIT%
};
#define NS (sizeof STEPS / sizeof STEPS[0])
%EXPECTED%

static unsigned char rol8(unsigned char v,int n){n&=7;return (unsigned char)((v<<n)|(v>>(8-n)));}
static unsigned char step_apply(unsigned char c, struct step s){
    unsigned char k=(unsigned char)(s.k & 0xFF);
    switch(s.op){case 0:return c^k;case 1:return (unsigned char)(c+k);
                 case 2:return (unsigned char)(c-k);case 3:return rol8(c,k);}
    return c;
}
int main(void){
    unsigned char in[256];
    if(!fgets((char*)in,sizeof in,stdin)){puts("nope.");return 1;}
    size_t n=strlen((char*)in);
    while(n && (in[n-1]=='\n'||in[n-1]=='\r')) in[--n]=0;
    if(n!=sizeof expected){puts("nope.");return 1;}
    for(size_t i=0;i<n;i++)
        if(step_apply(in[i], STEPS[i%NS]) != expected[i]){puts("nope.");return 1;}
    puts("Wire format valid. That input is the flag.");
    return 0;
}
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", default="AURA{p4dding_is_where_the_model_slips}")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    fb = a.flag.encode()
    expected = bytes(transform(c, i) for i, c in enumerate(fb))
    if a.selftest:
        assert all(invert(transform(c, i), i) == c for i in range(NS) for c in range(256))
        assert bytes(invert(expected[i], i) for i in range(len(expected))) == fb
        rod = steps_rodata()
        assert len(rod) == 8 * NS, "stride not 8!"
        # confirm padding bytes are the 3 after each op
        for j in range(NS):
            assert rod[j*8+1:j*8+4] == b"\x00\x00\x00", "padding not where expected"
        print(f"padded-struct OK: {a.flag} expected={expected.hex()} stride={len(rod)//NS}")
        return
    steps_init = ",\n".join(f"    {{ {op}, 0x{k:08X} }}" for op, k in STEPS)
    c = (C_TEMPLATE.replace("%STEPS_INIT%", steps_init)
                   .replace("%EXPECTED%", carr("expected", expected)))
    sys.stdout.write(c)
    sys.stderr.write(f"[gen] flag={a.flag!r} expected={expected.hex()} stride=8\n")

if __name__ == "__main__":
    main()
