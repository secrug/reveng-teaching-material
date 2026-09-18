# Breakout — Writeup

**Category:** pwn (+ rev) · **Difficulty:** insane · **Flag:** server-side
`flag.txt` (per-instance)

## TL;DR

The AURA-7 coprocessor runs your uploaded ASP program in a "sandbox" — registers
and a 64-byte data memory. But the memory index is a full byte (0–255) with **no
bounds check**, and a function pointer (`trap`) sits in the struct *immediately
after* the 64-byte array. So a `ST` to mem index 64–71 overwrites `trap`. Write
`&win` across those 8 indices, then execute `TRAP`. VM escape → native code.

This is the capstone: **rev** to recover the ISA and spot the missing bounds
check, **pwn** to craft the escape program.

## 1. Recover the ISA (rev)

Five opcodes: `HALT`, `MOVI r,imm`, `LD d,idx` (`reg[d]=mem[reg[idx]]`),
`ST idx,s` (`mem[reg[idx]]=reg[s]`), `TRAP` (`trap(vm)`). Straightforward once you
read the dispatch loop.

## 2. Find the escape (rev → pwn)

The struct:

```c
struct asp { unsigned char reg[16];   // offset 0
             unsigned char mem[64];    // offset 16..79
             void (*trap)(struct asp*);// offset 80
           };
```

`mem[64]` runs from struct offset 16 to 79; `trap` (8-byte aligned) is at offset
80. So **`mem[64]` is `trap` byte 0** — and `ST`/`LD` index `mem[reg[idx]]` with
`reg[idx]` up to 255, with no check. `mem` index 64..71 is a read/write window
onto the `trap` pointer. That adjacency is a struct-layout fact (offset 80,
naturally aligned — no padding), not a fragile stack coincidence.

## 3. Craft the escape program (pwn)

For each byte `k` of `&win` (little-endian): set a register to index `64+k`, set
another to the address byte, `ST`. Eight times, then `TRAP`:

```
for k in 0..7:
    MOVI r0, 64+k          # mem index onto trap byte k
    MOVI r1, (&win >> 8k) & 0xff
    ST   r0, r1            # mem[reg0] = reg1  -> trap[k]
TRAP                        # trap == &win  ->  win() -> cat flag.txt
HALT
```

74 bytes. `&win` is fixed (`-no-pie`), read via `nm asp-escape`.
`solution/exploit.py` emits this program, sends it, and reads the flag.

## 4. What's verified where

- **Verified on the authoring machine** (`src/asp_escape_model.py`): a faithful
  interpreter model with the real struct layout (mem index 64..71 aliases the
  trap pointer) runs the generated 74-byte program and confirms `trap` becomes
  `&win` and `TRAP` dispatches to it. The escape *logic* is sound.
- **Verified on build** (`healthcheck.sh`, Linux): `&win` is read from the
  compiled non-PIE binary, the program is fired at the live process, and the flag
  is read back. The struct offset (mem[64] → trap) is also asserted from the
  binary's layout.

## 5. Why this is hard for AI (the targeted failure)

This is the suite's hardest, because it stacks two failure modes.

1. **A novel machine, escaped by understanding its C host.** You must reverse the
   ASP ISA (no public precedent — the S6/S9 wall) *and* reason about the **C
   struct layout of the interpreter** to see that `mem[64]` aliases `trap`. That
   second step is the pwn insight: the sandbox is only as strong as the memory
   layout around it, and the model has to connect an in-VM operation (`ST`) to an
   out-of-VM consequence (overwriting a host function pointer). Cross-abstraction
   reasoning like that is exactly what unguided agents miss.
2. **Long, brittle chain.** Recover ISA → find the unchecked index → compute the
   struct offset → craft byte-exact bytecode that writes an 8-byte pointer one
   byte at a time → pivot via `TRAP`. Any early error yields silence, not a
   near-miss. The benchmark pattern (novel + memory-corruption + multi-step) is
   the worst case for automation.

The human path is the whole course, end to end: read the machine (S2–S3),
understand the memory model (S4–S5), find the missing check (S9 triage), and turn
an OOB write into control flow (S7). A human directing an AI — "the ST index
isn't bounds-checked and `trap` is right after `mem`; write &win to mem[64..71]
and TRAP" — gets there; an unguided agent, per the benchmarks, does not.

## 6. Mitigations

Bounds-check the VM memory index (`if (reg[idx] >= sizeof mem) fault;`) — the
single missing line. Structurally: don't place host pointers adjacent to
attacker-writable VM memory; keep interpreter control state in a separate
allocation or behind a guard page. A real VM sandbox treats every guest index as
hostile, which is the lesson.
