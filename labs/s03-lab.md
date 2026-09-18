# Lab 3 — Reconstruction

**Time:** 40 min (incl. 10-min matching game) · **Pack:** `s03/recon1`…`recon4`,
matching-game cards

---

## Warm-up game — Match asm to C (10 min, pairs, paper)

Six assembly listings, six C snippets, shuffled. Match them. Fastest correct pair
wins bragging rights. Forces shape-recognition over line-reading.

Pairs cover: an `if`, an `if/else`, a `while`, a `for`, a `do/while`, and a
`cmov` ternary — the six shapes from Teach A. The `do/while` (no leading jump) and
the `cmov` (no branch) are the two that trip everyone; that's intended.

---

## Core — Recover `recon1` and `recon2`

Write equivalent C for `recon1` (an if/else) and `recon2` (a counted `for` loop).

**Deliverable:** compilable C that matches the behaviour. Names can be invented;
structure must match.

### Solution outline

`recon1`: a signed comparison with the inverted jump (`jle` for source `>`) — the
common trap. `recon2`: a `for(i=0;i<n;...)` with init/test-at-bottom/inc shape.
Accept any C that reproduces the control flow; check they got the comparison
*direction* right (the inverted-jump lesson).

---

## Stretch — `recon3` with a CFG first

`recon3` is a nested loop with an early `break`. **Draw the CFG before writing any
C.** Then write the C.

**Deliverable:** hand-drawn CFG + the C. Students who skip the CFG will get lost —
let them, then point at the CFG.

### Solution outline

Outer loop, inner loop, a conditional `break` out of the inner (a `jmp` to the
block after the inner loop, not the outer test). The **loop bound is `<=`
(`jle`)** — this is the exact off-by-one the Falsification Drill exploits, so the
correct recovery is `i <= n`, iterating n+1 times. Students who write `i < n` have
made the same error the model will; note it, it primes the drill.

---

## Boss — `recon4`, branchless (explain-back)

`recon4` is a `do/while` containing a `cmov`, compiled `-O2`. Recover it, and
answer: **why is there no `jmp` at the top of the loop, and where did the `if`
inside go?**

**Deliverable:** the C + the two answers, to a neighbour, notes closed.

### Solution outline

No top jump because `do/while` tests at the bottom. The vanished `if` is a `cmov`
— a conditional move with no branch. A student who "can't find the if" has learned
the real lesson: decisions don't always have jumps.

---

## TA notes

The CFG-first discipline on Stretch is the transferable skill. The `recon3`
off-by-one is deliberately the same one the drill catches the model making — if a
student hits it themselves, that's gold: "you just made the exact mistake we're
about to catch the AI making. How would you catch *yourself*?"
