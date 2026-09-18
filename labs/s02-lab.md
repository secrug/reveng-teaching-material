# Lab 2 — Be the CPU

**Time:** 40 min · **Pack:** `s02/trace1`…`trace3`, `decode.txt` · **First 12
minutes: laptops closed.**

---

## Core — Hand-trace `trace1` (target: everyone)

On the paper register grid, hand-execute the 20 instructions of `trace1` (no
memory access, arithmetic/logic/mov only). Fill the grid one instruction at a
time. **Then** verify in gdb:

```bash
gdb ./trace1
(gdb) starti
(gdb) si          # step one instruction
(gdb) info registers rax rbx rcx rdx
```

**Deliverable:** your paper grid, and — if it disagreed with gdb — the *first*
instruction where they diverged and why.

### Solution outline

`trace1` is built (BUILD-PLAN §S2) to exercise: `xor reg,reg` zeroing, `lea` as
arithmetic, `imul`, shifts, and one `mov eax, …` that zero-extends. The intended
"gotcha" divergence is the zero-extension. The skill being graded is *bisection*:
finding the first divergence, not re-doing the whole trace.

### Watch for

- Students assuming they're wrong when gdb disagrees. Make them find *which*
  instruction — often gdb reveals *their* zero-extension error, which is the
  point.
- `lea` misread as a memory load. `lea rbx,[rax+rax*2]` is `rbx = 3*rax`, no
  memory touched.

---

## Stretch — Memory, `lea`, and hand-decoding

1. Hand-trace `trace2` (adds memory loads/stores and `lea` address math); verify
   in gdb with `x/gx` on the addresses it touches.
2. From `decode.txt`, hand-decode 5 raw-byte instructions using reference card #2.

**Deliverable:** the trace grid + the 5 decoded instructions with the byte→mnemonic
reasoning.

### Solution outline

Decoding targets are chosen to be card-decodable: a REX-prefixed `mov`, a
`mov`-immediate, an `add r/m, r`, a `jmp rel8`, and one ModRM with a SIB byte
(`[base+index*scale]`) — enough to see the addressing-mode encoding without a full
decoder. Provide the annotated answers in the solutions repo, byte by byte.

---

## Boss — The one that changes the answer (explain-back)

`trace3` contains one instruction whose **operand-size behaviour** changes the
final register state — remove or resize it and the result differs. Find that
instruction, and explain in one sentence why its size matters.

**Deliverable:** the instruction, the one-line explanation, delivered to a
neighbour with notes closed.

### Solution outline

It's a `mov eax, <val>` (or `add eax,…`) that zero-extends into `rax`, where a
later 64-bit op depends on the upper half. Replace with the 64-bit form and the
final `rax` changes. The explanation must name *zero-extension of 32-bit writes* —
if they say anything else, they found a coincidence, not the cause.

---

## TA notes

Enforce the closed-laptop 12 minutes physically — walk the room. The hand-trace
is the entire point; a student who goes straight to `si` learns nothing today. The
"be the CPU" muscle is what makes S3's block-reading possible.
