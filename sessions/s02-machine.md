# Session 2 — The machine: registers, memory, instruction semantics

**The one idea:** a CPU is a state machine. Every instruction is a total function
from (registers, memory, flags) to (registers, memory, flags). Nothing more
mysterious is happening, ever.

---

## Outcomes

1. Name the x86-64 general registers and their 32/16/8-bit aliases, and explain
   what writing `eax` does to `rax`.
2. Read `[base + index*scale + disp]` and compute the effective address.
3. Distinguish `mov` from `lea` and say why the difference matters.
4. Hand-execute a 20-instruction sequence and predict the final register state.
5. Decode an instruction from raw bytes using a reference card.
6. Explain why an LLM's register trace failed, in terms of operand size or flags.

---

## Prep checklist

- [ ] `s02/` pack: `trace1`–`trace3`, `sizes`, `lea_vs_mov`, `decode.txt`
- [ ] Reference card **#2 (x86-64)** — students should have it from S1; spares
- [ ] gdb with pwndbg, `set disassembly-flavor intel` **verified in the image**
- [ ] Register-state grid printed, one per student (see `handouts/`)
- [ ] **ARM Macs:** this is the first session where emulation hurts. Tier-1
      fallback must be live *today* — see `infra/SETUP.md` §3
- [ ] Casts: `s02-demo1.cast`, `s02-demo2.cast`

---

## 0:00 — Warm-up (15 min)

Retrieval, not revision. Five questions on the board; students write answers,
then we settle them by *doing*, not telling.

1. Name two things destroyed by compiling with `-O2`.
2. `file` says "data". What do you do next?
3. Why can't a perfect decompiler exist?
4. You see the bytes `41 55 52 41`. What are they, and what did you assume?
5. From the open-questions board: what didn't the length field in `aura-fw.bin`
   match?

Settle Q4 with `xxd` on screen. Settle Q5 by pointing at the board — the open
question is still open. That is deliberate: it models that real questions stay
open for weeks.

---

## 0:15 — Cold open (10 min)

On screen, no context:

```asm
mov    eax, 0xfffffffe
mov    ebx, 3
imul   eax, ebx
movsx  rcx, eax
mov    rdx, 0xfffffffffffffffa
cmp    rcx, rdx
```

**Question:** after `cmp`, is the zero flag set?

Written prediction, two minutes. Most will say yes (both are −6). Some will spot
the sign-extension. A few will get lost in the hex.

Don't resolve it. Resolve it at 2:55, in gdb, with everyone watching the flags
register change.

---

## 0:25 — Teach A: the state machine (35 min)

### A1 — The state (10 min)

Draw the machine on the board and leave it up:

```
 ┌─────────────── CPU ───────────────┐      ┌──── MEMORY ────┐
 │ rax rbx rcx rdx rsi rdi rbp rsp   │      │  one flat      │
 │ r8  r9  r10 r11 r12 r13 r14 r15   │◀────▶│  array of      │
 │ rip                               │      │  bytes         │
 │ flags: ZF SF CF OF                │      │  addressed     │
 └───────────────────────────────────┘      │  0 .. 2^48     │
                                            └────────────────┘
```

Three claims, stated flatly:

1. **That's all the state there is.** Sixteen integer registers, an instruction
   pointer, some flags, and memory.
2. **Memory has no types.** A byte is a byte. `int`, `float`, `char*` and `struct
   foo` are fictions the *compiler* maintained and then discarded. Recovering
   those fictions is Session 5.
3. **`rip` is just a register** that usually increments. Everything interesting
   in security and RE comes from the "usually".

### A2 — Registers and the operand-size trap (12 min)

The alias structure, on the board:

```
 63                    31        15     7    0
 ├──────────────────────┼─────────┼──────┼────┤
 │                     rax                    │
                        │        eax          │
                                  │    ax     │
                                        │ al  │
```

Then the trap, demonstrated live because nobody believes it otherwise:

```bash
gdb ./sizes
(gdb) b main
(gdb) run
# mov rax, 0xffffffffffffffff  → rax = 0xffffffffffffffff
# mov eax, 1                   → rax = 0x0000000000000001   ← upper 32 zeroed!
# mov ax,  2                   → rax = 0x0000000000000002   ← upper bits kept
# mov al,  3                   → rax = 0x0000000000000003   ← upper bits kept
```

> "Writing a 32-bit register zeroes the top half. Writing 16 or 8 bits doesn't.
> There's no principle here — it's a decision AMD made in 2000 for reasons about
> instruction encoding. You just have to know it.
>
> Write it on your card. This is the single most common source of 'my trace
> disagrees with gdb', and it is also — you'll see at 2:55 — where language
> models fall over, for exactly the same reason: it's an arbitrary rule, not a
> pattern."

### A3 — Instructions worth knowing (13 min)

Not the full ISA. The ~20 that are 90% of real code, straight off card #2:
`mov`, `movzx`/`movsx`, `lea`, `add`/`sub`, `imul`, `and`/`or`/`xor`/`not`,
`shl`/`shr`/`sar`, `cmp`, `test`, `push`/`pop`, `call`/`ret`, `jmp`/`jcc`, `nop`.

Two idioms to name now, because they appear in every binary from here on:

- `xor eax, eax` — sets to zero. Shorter encoding than `mov eax, 0`. Not obfuscation.
- `test rax, rax` — sets flags from `rax & rax`, i.e. "is it zero?" Not `cmp rax, 0`.

Then addressing modes, worked on the board with real numbers:

```
 [rbx]                  → M[rbx]
 [rbx + 8]              → M[rbx + 8]
 [rbx + rcx*4]          → M[rbx + 4*rcx]          ← array of 4-byte things
 [rbx + rcx*8 + 16]     → M[rbx + 8*rcx + 16]     ← array of 8-byte things at +16
 [rip + 0x2e4a]         → M[address of next instr + 0x2e4a]   ← globals
```

> "That `*4` and `*8` is free information. The machine is telling you the element
> size of an array. In Session 5 that's how you'll recover types you were never
> given."

Finally `lea` vs `mov`, live:

```asm
lea rax, [rbx+8]    ; rax = rbx + 8          (compute the address)
mov rax, [rbx+8]    ; rax = M[rbx + 8]       (go and get the value)
```

> "`lea` is the compiler's pocket calculator. When you see `lea rax, [rdi+rdi*2]`
> that's not an address at all — that's `rdi * 3`. Compilers do arithmetic in the
> addressing unit because it's fast. Don't be fooled into thinking every `lea` is
> about memory."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: Be the CPU (40 min)

Full spec: [`labs/s02-lab.md`](../labs/s02-lab.md).

**The first 12 minutes are laptops closed.** This is non-negotiable and you must
enforce it physically — walk the room. Paper register grid, 20 instructions, hand
trace. Then open gdb and check.

- **Core** — trace `trace1` (20 instrs, no memory) by hand; verify in gdb.
- **Stretch** — trace `trace2` (uses memory and `lea`); decode 5 instructions
  from raw bytes with card #2.
- **Boss** — `trace3` contains one instruction whose 32-bit write behaviour
  changes the result. Find it, and write the one-line explanation. (Explain-back.)

The moment to watch for: a student's hand trace disagrees with gdb and they
assume *they* are wrong. Often they are. But make them find *which instruction*
diverged rather than discarding the whole trace. That diagnostic move — bisect to
the first divergence — is the debugging skill the session is really teaching.

---

## 1:50 — Teach B: live demo — the CPU has no idea what you meant (25 min)

Run `lea_vs_mov` under gdb, register window up, stepping with `si`, asking
**"what will `rax` be?"** before every single instruction. Let the room answer
out loud. Get it wrong yourself at least once.

**Scripted wrong turn.** Reach an instruction like:

```asm
mov eax, DWORD PTR [rdi+0x4]
```

Say "so that's the second field, a 4-byte thing" — then stop.

> "Wait. I said 'field'. Where did I get that? There's no struct here. I saw
> `[rdi+4]` and my brain supplied a struct because that's what I *usually* see.
>
> It might be a struct. It might be an array of ints and this is index 1. It
> might be the high half of an 8-byte value. The machine doesn't know and neither
> do I — yet. I've just caught myself doing the exact thing I'm going to show you
> a language model doing in forty minutes."

This is the highest-value ninety seconds of the session. The lecturer models
catching their own pattern-match. Do not cut it.

Finish by showing the same C compiled `-O0` vs `-O2` and stepping both: at `-O0`
every variable is in memory and the code is legible; at `-O2` everything lives in
registers and there is no `mov` to be seen. Same program. Read both.

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: instruction archaeology (30 min)

No AURA-7 today — students need volume on raw instruction semantics, and AURA-7
is too big to read without the tools of S3. Say so, so it doesn't look like drift.

Students take `objdump -d` of a small binary and annotate **every line** of one
function in plain English, one comment per instruction. About 30 instructions.

```
  mov  eax, DWORD PTR [rbp-0x8]   ; load the local at rbp-8 into eax
  add  eax, eax                   ; eax = eax * 2
  ...
```

Tedious on purpose. This is the last time they will annotate line by line — from
S3 they read in blocks — and doing it once at full resolution is what makes block
reading possible later.

Seed the drill: **"give a model `trace3` and ask for the final register state.
Keep its answer."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** Model output: *"After this sequence, `rax` = 0x1122334455667788."*

1. *State it.*
2. *What would falsify it?* — `info registers rax` at the final instruction. One
   observation, unambiguous. Get the room to say this.
3. *Observe.* Run it. The upper 32 bits are zero: `0x0000000055667788`.
4. *Verdict.* **Wrong.** Reason: the model tracked the *arithmetic* correctly but
   missed that a 32-bit write zero-extends. It reasoned about values, not about
   the machine. Record it.

> "Notice what kind of error that is. It's not sloppy. The arithmetic was right.
> It failed on an arbitrary architectural rule — exactly the thing that isn't
> derivable from first principles and has to be *known*. That's a pattern. Watch
> for it over the next five months."

**Cold-open reveal.** Run the morning's sequence in gdb, flags register visible.
`movsx` sign-extends `0xfffffffa` to `0xfffffffffffffffa` — so ZF **is** set.
Both were −6 after all. Then the sting: change `movsx` to `movzx` and rerun. ZF
clears. One letter.

> "One letter. And 'both are minus six' was the right *intuition* and would have
> given you the wrong *answer* if I'd written `movzx`. Intuition proposes.
> Evidence decides."

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 2 | Final `rax` = 0x1122334455667788 after the trace | ✗ Wrong | Correct arithmetic; missed that 32-bit register writes zero the upper half — an arbitrary ISA rule, not an inferable pattern |

---

## Lecturer notes

**This is the session where ARM-Mac emulation bites.** Single-stepping under
qemu-user is slow and pwndbg's register diffing can misbehave. Have tier-1
(shared x86-64 box) working today or the lab fails for a third of the room.

**Pace risk: A3 overruns.** The instruction list tempts completeness. It is a
*card*, not a lecture — point at the card, do the two idioms and the addressing
modes properly, move on.

**Pointers.** `[rax]` is a pointer dereference and someone will say so. Confirm
it, then defer: "yes — and in Session 5 we'll use the `*4` and `*8` to work out
what it points *to*. Today it's just arithmetic."

**Running long.** Cut Boss tier, then the `-O0`/`-O2` comparison at the end of
Teach B. Protect the 12 laptops-closed minutes in Lab A — that block is the
session.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-2)

- **Read:** CS:APP §3.1–3.5 (30 min).
- **Do:** microcorruption, tutorial + first two levels. Different ISA on purpose
  — if the *concept* transfers, you've learned the concept.
- **Crackme:** crackmes.one difficulty 1, "arithmetic" tag.
- **Self-check:** 5 questions, answers included.
