# The AI Scoreboard

**Print this large. Put it on the wall. Fill in one row every session.**

The scoreboard is the course's central evidence-gathering instrument. Every
session, a model produces an analysis of that session's artifact, and the class
produces *evidence* that confirms or refutes one specific claim (the Falsification
Drill). The verdict — and, crucially, **the reason** — goes here.

By Session 10 this table is not a list of anecdotes. It is a class-derived,
evidence-backed map of *where and why* AI fails on binaries. Session 10's warm-up
reads it as a body of evidence and finds the single pattern underneath all of it.

The **reason column is the valuable one.** "AI was wrong" is worthless. "AI
summed struct field sizes and omitted the alignment padding, because the padding
is invisible in the source it was trained on" is a transferable law.

---

## How to run the drill (fixed script, every session)

1. **State the claim** in one sentence, with its offset or symbol.
2. **Name the observation that would falsify it** — a register value, a memory
   dump, a breakpoint hit, a byte at an offset. *(This step is the whole
   exercise. Get it from the room, not from the lecturer.)*
3. **Make the observation.**
4. **Record the verdict here, with the reason.**

Not an opinion. Not a second model's opinion. Evidence.

---

## The board

| S | The claim (what the model said) | Verdict | The reason it failed (the transferable part) |
|---|---|---|---|
| 1 | `auractl` compares the licence to a hardcoded `.rodata` string | ✗ | Pattern-matched to the common tutorial shape; no such string exists; real path uses `memcmp` on a computed value |
| 2 | Final `rax` = `0x1122334455667788` after the trace | ✗ | Correct arithmetic; missed that a 32-bit write zeroes the upper half — an arbitrary ISA rule, not an inferable pattern |
| 3 | `recon3`'s loop is `for (i=0; i<n; i++)` | ✗ | Off-by-one: binary uses `jle` (≤); model produced the more common `<`. Plausible, compiles, wrong. Caught by counting breakpoint hits |
| 4 | AURA-7 handler is `int f(char *s)` — one argument | ✗ | Missed an argument: `rsi` is read before write ⇒ ≥2 args. Model stopped at the recognisable `strlen(rdi)` |
| 5 | `aura_config.checksum` is at offset 21 | ✗ | Dropped alignment padding: summed field sizes, omitted the 3-byte hole after `mode`. Real offset 24. Systematic — predicted in advance |
| 6 | The licence check lives in `check_license` | ✗ | Decoy: both decompiler and LLM reported a true fact about the bytes (returns constant) but neither models *intent*. Real check inlined in caller; found via xref (return unused) |
| 7 | Model's gdb script logs the accumulator each iteration | ✗ | Subtly wrong tooling: plausible gdb Python, wrong detail (register / sample point / off-by-one). 90% right, 10% makes every value a lie |
| 8 | `LD_PRELOAD` a `strcmp`→0 bypasses the check | ✗ | Textbook answer for the wrong binary: comparison is inlined, no `call strcmp@plt` exists. Interposition only catches PLT-crossing calls |
| 9 | The licence algorithm is CRC32 (or rolling hash, wrong constant) | ✗ | Right genre, wrong specifics: pattern-matched the "licence hash" family. Diverges from the true recurrence at byte 2. Caught only because the class had recovered the real algorithm by hand |
| 10 | (Table B's model) `enigma`'s algorithm is [wrong] | ✗ | Same failure, discovered by students racing it: right genre / narrated the decoy. Table B couldn't recover; Table C could — because Table C could read the evidence |

*(The verdicts above are the expected/exemplar outcomes. Fill the board with what
your class actually observes — and if a drill produces a different or even a
correct result against a newer model, record that honestly. A shifted boundary is
a finding, not a failure; see the S10 contingency.)*

---

## The pattern (revealed in S10, not before)

Don't pre-empt this — let the class find it in the S10 warm-up. But for the
lecturer, the through-line every row shares:

> The model produces the **statistically likely** answer, and it breaks precisely
> where this binary **departs from the likely** — the arbitrary rule, the padding,
> the decoy, the custom constant, the specific offset. And in every single case it
> was caught with **evidence** the students could read because they built the
> skill by hand.

That is not nine anecdotes. It is one law, derived nine times, and it is the
entire argument of the course:

**Fluency is not correctness. A generator is not a verifier. You are the
verifier — and only because you know the fundamentals.**
