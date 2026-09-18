#!/usr/bin/env python3
"""Parse the committed signal-lock.c, extract prog[]/expected[], and run them
through the validated ASP VM to confirm the reference flag is accepted and a
mutation is rejected. Guards against a C-emission/templating bug in gen.py."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from asp_reference import run_vm  # validated interpreter

C = pathlib.Path(__file__).parents[1] / "challenges/rev-signal-lock/src/signal-lock.c"
txt = C.read_text()

def arr(name):
    m = re.search(name + r"\[\]\s*=\s*\{([^}]*)\}", txt)
    return bytes(int(x) for x in m.group(1).split(","))

prog = arr("prog"); expected = arr("expected")
FLAG = b"AURA{tta_s1gnal_l0ck}"

assert run_vm(prog, FLAG, expected) is True, "committed C rejects the correct flag!"
bad = bytearray(FLAG); bad[7] ^= 1
assert run_vm(prog, bytes(bad), expected) is False, "committed C accepts a mutation!"
assert run_vm(prog, FLAG + b"x", expected) is False, "committed C accepts too-long!"
print(f"COMMITTED C OK: prog={len(prog)}B expected={expected.hex()} flag accepted, mutations rejected")
