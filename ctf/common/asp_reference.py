#!/usr/bin/env python3
"""Validate the Signal Lock TTA design end-to-end before committing to C.

Proves: (1) the transform round-trips, (2) the assembled bytecode run on the
correct flag passes the VM, (3) a wrong input fails, (4) the solver recovers the
flag by inverting only what's observable (expected[] + the 3 constants)."""

MASK = 0xFF
def rol8(v, n): n &= 7; return ((v << n) | (v >> (8 - n))) & MASK
def ror8(v, n): n &= 7; return ((v >> n) | (v << (8 - n))) & MASK

# ---- the per-byte transform the TTA program computes ----
K1, K2, K3 = 0x5A, 0x1B, 0x3C
def transform(c, i):
    u = c ^ K1
    u = rol8(u, i & 7)
    u = (u + (i * K2)) & MASK
    u = u ^ K3
    return u
def inverse(t, i):
    u = t ^ K3
    u = (u - (i * K2)) & MASK
    u = ror8(u, i & 7)
    return u ^ K1

# ---- the ASP-mini transport-triggered VM ----
# opcodes: 0x00 HALT | 0x01 MOV dst,src | 0x02 MOVI dst,imm
# ports:
#   0x00-0x0F  R0..R15 storage
#   0x10 INPUT (read -> next input byte, advance cursor; past end sets underflow)
#   0x11 CHECK (write -> compare to expected[out_cursor], advance; mismatch=fail)
#   0xA0 ADD.A(w latch) 0xA1 ADD.Btrig(w -> R=A+B) 0xA2 ADD.R(read)
#   0xB0 XOR.A          0xB1 XOR.Btrig(w -> R=A^B)  0xB2 XOR.R
#   0xC0 ROL.V          0xC1 ROL.Ntrig(w -> R=rol8(V,n)) 0xC2 ROL.R
OP_HALT, OP_MOV, OP_MOVI = 0x00, 0x01, 0x02

def run_vm(prog, inp, expected):
    reg = [0] * 256
    a = {'ADD':0,'XOR':0,'ROL':0}; r = {'ADD':0,'XOR':0,'ROL':0}
    incur = [0]; outcur = [0]; fail = [False]

    def rd(p):
        if p == 0x10:
            if incur[0] >= len(inp): fail[0] = True; return 0
            v = inp[incur[0]]; incur[0] += 1; return v
        if p == 0xA2: return r['ADD']
        if p == 0xB2: return r['XOR']
        if p == 0xC2: return r['ROL']
        return reg[p]

    def wr(p, v):
        v &= MASK
        if p == 0x11:
            if outcur[0] >= len(expected) or v != expected[outcur[0]]: fail[0] = True
            outcur[0] += 1; return
        if p == 0xA0: a['ADD'] = v; return
        if p == 0xA1: r['ADD'] = (a['ADD'] + v) & MASK; return
        if p == 0xB0: a['XOR'] = v; return
        if p == 0xB1: r['XOR'] = (a['XOR'] ^ v) & MASK; return
        if p == 0xC0: a['ROL'] = v; return
        if p == 0xC1: r['ROL'] = rol8(a['ROL'], v); return
        reg[p] = v

    pc = 0
    while pc < len(prog):
        op = prog[pc]
        if op == OP_HALT: break
        if op == OP_MOV:  wr(prog[pc+1], rd(prog[pc+2])); pc += 3
        elif op == OP_MOVI: wr(prog[pc+1], prog[pc+2]); pc += 3
        else: raise ValueError(f"bad op {op:#x} at {pc}")
    ok = (not fail[0]) and incur[0] == len(inp) and outcur[0] == len(expected)
    return ok

def assemble(n):
    """Unrolled straight-line program processing n input bytes."""
    R0 = 0x00; INPUT = 0x10; CHECK = 0x11
    p = []
    for i in range(n):
        p += [OP_MOV,  R0,   INPUT]         # R0 = c
        p += [OP_MOV,  0xB0, R0]            # XOR.A = R0
        p += [OP_MOVI, 0xB1, K1]            # XOR.R = R0 ^ K1
        p += [OP_MOV,  R0,   0xB2]
        p += [OP_MOV,  0xC0, R0]            # ROL.V = R0
        p += [OP_MOVI, 0xC1, i & 7]         # ROL.R = rol8(R0, i&7)
        p += [OP_MOV,  R0,   0xC2]
        p += [OP_MOV,  0xA0, R0]            # ADD.A = R0
        p += [OP_MOVI, 0xA1, (i * K2) & MASK]  # ADD.R = R0 + i*K2
        p += [OP_MOV,  R0,   0xA2]
        p += [OP_MOV,  0xB0, R0]            # XOR.A = R0
        p += [OP_MOVI, 0xB1, K3]            # XOR.R = R0 ^ K3
        p += [OP_MOV,  R0,   0xB2]
        p += [OP_MOV,  CHECK, R0]           # compare to expected[i]
    p += [OP_HALT]
    return bytes(p)

def make_expected(flag_bytes):
    return bytes(transform(c, i) for i, c in enumerate(flag_bytes))

# ---- validation (self-test; runs only when executed directly, not on import) ----
def _selftest():
    FLAG = b"AURA{tta_s1gnal_l0ck}"
    n = len(FLAG)
    prog = assemble(n)
    expected = make_expected(FLAG)

    # 1. transform round-trips over all inputs
    assert all(inverse(transform(c, i), i) == c for i in range(256) for c in range(256)), "transform not invertible!"
    # 2. correct flag passes the VM
    assert run_vm(prog, FLAG, expected) is True, "correct flag rejected!"
    # 3. wrong inputs fail (mutation; wrong length either way)
    bad = bytearray(FLAG); bad[5] ^= 1
    assert run_vm(prog, bytes(bad), expected) is False, "mutated flag accepted!"
    assert run_vm(prog, FLAG + b"!", expected) is False, "too-long accepted!"
    assert run_vm(prog, FLAG[:-1], expected) is False, "too-short accepted!"
    # 4. solver recovers flag from ONLY expected[] + (K1,K2,K3)
    recovered = bytes(inverse(expected[i], i) for i in range(len(expected)))
    assert recovered == FLAG, f"solver failed: {recovered!r}"
    return FLAG, n, prog, expected, recovered


if __name__ == "__main__":
    FLAG, n, prog, expected, recovered = _selftest()
    print("ALL CHECKS PASSED")
    print(f"flag           : {FLAG.decode()}")
    print(f"flag length    : {n}")
    print(f"program bytes  : {len(prog)} ({len(prog)//3} instructions incl HALT)")
    print(f"expected[] hex : {expected.hex()}")
    print(f"recovered flag : {recovered.decode()}")
    print(f"K1,K2,K3       : {K1:#04x},{K2:#04x},{K3:#04x}")
