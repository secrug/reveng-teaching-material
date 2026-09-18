# Session 3 — Control flow: decisions and loops in machine code

**The one idea:** the compiler has a small, finite vocabulary for turning your
control structures into jumps. Learn the vocabulary and you read it backwards.

---

## Outcomes

1. Explain what `cmp` and `test` actually do, and which flag each `jcc` reads.
2. Split a disassembly into basic blocks and draw the CFG.
3. Recognise the compiled shape of if/else, while, for, do-while, `&&`/`||`, and
   the ternary→`cmov` rewrite.
4. Identify a jump table, find its bounds check, and enumerate its targets.
5. Recover readable C from ~40 lines of assembly.
6. Name an off-by-one in a model's reconstruction and prove it with a breakpoint.

---

## Prep checklist

- [ ] `s03/` pack: `shapes` (6 functions), `loops`, `dispatch`, `recon1`–`recon4`
- [ ] Reference card **#2** in hand; card **#5 (methodology)** not yet
- [ ] Matching-game printouts: 6 asm listings + 6 C snippets, cut up, shuffled,
      one set per pair of students
- [ ] Casts: `s03-demo1.cast`, `s03-demo2.cast`

---

## 0:00 — Warm-up (15 min — the longest of the course)

Four weeks have passed since the machine model was introduced and there is no
homework bridging them. Budget the full fifteen and do it properly.

**Live, on the board, no slides.** Students hand-trace 8 instructions covering
exactly the S2 sticking points:

```asm
mov  rax, 0x100
mov  eax, 0x2               ; ← what is rax now?
lea  rbx, [rax+rax*2]       ; ← rbx = ?
xor  rcx, rcx               ; ← rcx = ?
mov  rdx, 0xdeadbeef
test rdx, rdx               ; ← what changed?
mov  esi, DWORD PTR [rsp]
add  rsi, rbx
```

Then verify in gdb on screen. Anyone whose `rax` is `0x102` after line 2 gets the
zero-extension rule re-explained — it will be several people, and that is exactly
what the warm-up is for.

---

## 0:15 — Cold open (10 min)

On screen:

```asm
  cmp  edi, 0x63
  ja   .Ldefault
  mov  eax, edi
  lea  rdx, [rip+0x1e4c]
  movsx rax, DWORD PTR [rdx+rax*4]
  add  rax, rdx
  jmp  rax
```

**Question:** where does `jmp rax` go? How many places can it go?

Written prediction. Nobody will have the full answer. Push for the *shape*: "an
indirect jump, so it's computed — computed from what?"

Deliberately unsettling: it is the first time control flow isn't visible in the
listing. Leave it up. Resolved at 2:55.

---

## 0:25 — Teach A: the compiler's vocabulary (35 min)

### A1 — Flags and conditional jumps (10 min)

`cmp a, b` computes `a - b` and **throws the result away**, keeping only flags.
`test a, b` computes `a & b`, same deal. That's it.

The table that matters, on card #2 and on the board:

| After `cmp a, b` | Jump | Taken when |
|---|---|---|
| | `je` / `jz` | a == b |
| | `jne` / `jnz` | a != b |
| **signed** | `jl` `jle` `jg` `jge` | a < b, ≤, >, ≥ |
| **unsigned** | `jb` `jbe` `ja` `jae` | a < b, ≤, >, ≥ |

> "Signed and unsigned use *different instructions* for the same comparison. So
> the assembly tells you the signedness of a variable whose type was destroyed at
> compile time. `ja` means the compiler knew it was unsigned. That's free type
> information, and you'll use it in Session 5."

Note `jb`/`ja` on the cold open — already a clue that `edi` was unsigned, or that
the compiler proved it non-negative.

### A2 — Basic blocks and the CFG (10 min)

Definition, kept short: a **basic block** is a straight-line run with one entry
and one exit. Blocks end at any jump, and start at any jump *target*.

Do one live on `shapes`, on the board:

```
        ┌──────────┐
        │ B0       │  cmp/jle ──┐
        └────┬─────┘            │
             │ fallthrough      │
        ┌────▼─────┐            │
        │ B1       │            │
        └────┬─────┘            │
             └──────────▶┌──────▼───┐
                         │ B2       │
                         └──────────┘
```

> "Stop reading assembly as a list of instructions. Read it as a graph of blocks.
> The instructions inside a block are almost never the interesting part — the
> *shape* is. This is the single biggest speed-up available to you and it's free."

### A3 — The six shapes (15 min)

Compiler Explorer, live, `-O0` then `-O1`. Build the pattern table on the board
as you go — students copy it, and it becomes their working reference:

| Source | Compiled shape |
|---|---|
| `if (c) A;` | test/cmp → `jcc` **over** A |
| `if (c) A; else B;` | `jcc` to B; A ends with `jmp` past B |
| `while (c) A;` | `jmp` to the test at the **bottom**; body above; test → `jcc` back up |
| `for (i=0;i<n;i++)` | init, then the while shape; `inc` at the bottom of the body |
| `do A while(c);` | body first, test at the bottom, `jcc` back. **No leading jump** — that absence is the tell |
| `c ? a : b` | often **no branch at all** — `cmov` |

Two things to stress:

**The inverted condition.** Source `if (x > 5)` compiles to `jle` — jump *away*
when the condition fails. Students misread this constantly for a month.

> "The compiler branches on the *negation*. Every time. If you read `jle` and
> think 'the source said less-or-equal', you have the program backwards."

**`cmov` and the missing branch.** Show `a > b ? a : b` at `-O2`:

```asm
cmp  edi, esi
cmovl edi, esi        ; no jump anywhere
```

> "There is a decision in this program and there is no branch in the machine
> code. If you're looking for control flow by looking for jumps, you'll miss it
> entirely. Compilers do this for speed, and it's also, incidentally, why
> constant-time cryptography is written this way."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: reconstruction (40 min)

Full spec: [`labs/s03-lab.md`](../labs/s03-lab.md).

Open with the **matching game**, 10 minutes, in pairs, paper only: 6 assembly
listings, 6 C snippets, match them. Fast, competitive, and it forces
shape-recognition rather than line-by-line reading. Then:

- **Core** — recover C from `recon1` and `recon2` (an if/else and a counted loop).
- **Stretch** — `recon3`: nested loop with an early `break`. Draw the CFG first,
  then write the C. Insist on the CFG *first*; students who skip it get lost and
  that lesson is worth the ten minutes it costs them.
- **Boss** — `recon4`: a `do`/`while` with a `cmov` inside, compiled `-O2`.
  (Explain-back: why is there no `jmp` at the top?)

---

## 1:50 — Teach B: live demo — the jump table (25 min)

**Target:** `auractl`'s command dispatcher. AURA-7 returns.

```bash
objdump -d auractl | less     # navigate to the dispatcher
```

Walk the cold-open instructions for real, live:

1. `cmp edi, 0x63` / `ja .Ldefault` — **the bounds check.** Point at it hard.
   > "That `ja` is the only thing standing between this program and jumping to an
   > address read from beyond the end of a table. When a bounds check like this
   > is missing or wrong, that's a vulnerability. We're not doing exploitation in
   > this course, but this is where it lives, and now you can see it."
2. `lea rdx, [rip+0x1e4c]` — the table's address. Compute it by hand at the
   board. **Scripted wrong turn:** get it wrong by forgetting that RIP-relative
   is relative to the *next* instruction, land in the middle of nothing, notice
   the values are garbage, go back, fix it. Narrate the recovery.
3. `movsx rax, [rdx+rax*4]` — 4-byte **signed offsets**, not addresses.
4. `add rax, rdx` / `jmp rax` — offset + table base = target.

Then dump the table and decode it live:

```bash
objdump -s -j .rodata auractl | grep -A8 1e4c
```

Work out two targets by hand at the board, then show the script that does the
rest, and be explicit about the division of labour:

> "I did two by hand so I know the format. Then I let a script do the other
> eighteen. That's the correct order — *understand, then automate.* Automating
> something you don't understand is how you get twenty confidently wrong answers
> instead of one."

End with the win: a list of AURA-7's command handlers. Put it on the board under
a new heading, **AURA-7 MAP**, next to the open questions from S1. Visible
progress.

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: enumerate the commands (30 min)

Students take the dispatcher themselves and produce the full command table:
index → handler address → guessed purpose (from strings and calls nearby).

Required output: a table with a **confidence column** — `certain` / `likely` /
`guess`. Enforce this. The habit of separating what you *know* from what you
*suspect* is the professional core of the whole discipline, and it is the thing
a model never does unprompted.

Seed the drill: **"ask a model to reconstruct `recon3`. Keep its C."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** The model's `recon3` reconstruction, typically:

```c
for (int i = 0; i < n; i++)        // model output
```

when the binary does:

```asm
cmp  eax, edx
jle  .Lbody                        // signed <=, so the loop runs i <= n
```

1. *State it.* "The model says `i < n`."
2. *What would falsify it?* — run with `n = 5` and count iterations, or break on
   the body and count hits. The room should produce this.
3. *Observe.* `b *0x…` then `run 5`, `info breakpoints` shows the hit count: 6.
4. *Verdict.* **Wrong — off by one.** Reason: `jle` vs `jl` is a one-character
   difference in the disassembly and an enormous difference in behaviour. The
   model produced the *statistically common* loop, not the one in front of it.

> "That is the most dangerous class of error you'll see all course. It's not
> absurd. It doesn't look wrong. It compiles, it runs, it's plausible, and it's
> wrong — and the only way you caught it was counting iterations. Off-by-ones in
> loop bounds are also, historically, one of the most productive sources of
> security bugs in the world."

**Cold-open reveal.** Already done in Teach B — close the loop explicitly: `jmp
rax` goes to one of 100 places, bounded by that `ja`, resolved through a table of
signed 32-bit offsets at `rip+0x1e4c`.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 3 | `recon3`'s loop is `for (i = 0; i < n; i++)` | ✗ Wrong (off-by-one) | Binary uses `jle` (≤), model produced the more common `<`. Plausible, compiles, wrong. Caught by counting breakpoint hits |

---

## Lecturer notes

**Students confuse `jle` with "the source said ≤".** It means the *negated*
condition jumped away. Say it three times in the session. Put it on the board and
leave it there.

**The CFG drawing feels like busywork to fast students.** It isn't, and the proof
is `recon3` — they will get lost without it and find it with it. Let that happen
rather than arguing.

**Someone asks about `switch` on strings or sparse cases.** Good question, short
answer: not all switches become tables. Sparse values become if-chains or binary
search trees. Show the difference in one minute on Compiler Explorer if time
allows; otherwise note it on the board as an open question.

**Running long.** Cut Boss tier, then the `cmov` example in A3 (but *mention*
that branchless decisions exist — a student who doesn't know `cmov` exists can
miss an entire decision in S9). Protect the jump-table demo.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-3)

- **Read:** CS:APP §3.6 (30 min) — control flow, properly.
- **Do:** write a program with a 10-case switch; compile `-O0`/`-O2`; find where
  the table stops being a table.
- **Crackme:** crackmes.one difficulty 1–2, "control flow" or "keygen-me" tag.
- **Self-check:** 5 questions, answers included.
