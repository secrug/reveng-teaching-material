# Session 7 — Dynamic analysis: running it and watching it

**The one idea:** static analysis tells you what a program *can* do; running it
under a debugger tells you what it *does*. A breakpoint is a hypothesis test, and
a patch is an experiment — not a victory.

---

## Outcomes

1. Describe a process's address space and what a syscall is (just-enough OS).
2. Explain how a software breakpoint actually works (an `int3` byte patch).
3. Use breakpoints, conditional breakpoints, watchpoints and a gdb script with
   intent.
4. Use `strace`/`ltrace` to see the syscall and library-call boundary.
5. Patch a branch on disk and predict, before running, what it changes.
6. Fix a subtly-wrong gdb script from a model using knowledge, not re-prompting.

---

## Prep checklist

- [ ] `s07/` pack: `licensed` (the break-and-observe target), `phone_home`
      (strace demo), `patchme`, and a `logcalls.py` reference script for the TA
- [ ] Reference card **#4 (gdb)** in hand — issued S6, spares today
- [ ] **ARM Macs:** second painful session. Tier-1 shared box mandatory —
      single-stepping under emulation is where it hurts most. `infra/SETUP.md` §3
- [ ] `strace`/`ltrace` present in the image (verify — `ltrace` is often missing)
- [ ] Casts: `s07-demo1.cast` (break/patch), `s07-demo2.cast` (strace)

---

## 0:00 — Warm-up (15 min)

1. What are the six standard decompiler failure modes? *(name any three)*
2. Decompiler and LLM — what do they have in common, in one word? *(generators)*
3. What kind of thing is evidence, by contrast?
4. In Ghidra, how do you find who calls a function?
5. Why was `check_license` a trap?

Keep it fast; today is heavy. This warm-up cements S6's thesis before it's built
on.

---

## 0:15 — Cold open (10 min)

Run `licensed`:

```
$ ./licensed
Enter licence key: AAAA-BBBB-CCCC-DDDD
Invalid licence.
```

**Question:** without reading much static, can you make this program print
"Valid"? Name your *first move* — where's the one place you'd set a breakpoint?

Written prediction. Most will say "break where it prints Invalid." Good instinct,
slightly wrong — you break *before* the decision, on the comparison. Resolve
through the session; formally at 2:55.

---

## 0:25 — Teach A: the live process and just-enough OS (35 min)

### A1 — What a running program is (12 min)

They have no OS course. Give them exactly what they need and no more.

Draw the address space on the board:

```
  0x7fff... ┌────────────┐ high
            │   stack    │ grows down  (S4 lives here)
            │     ↓      │
            │            │
            │     ↑      │
            │    heap    │ grows up    (malloc, S5)
            ├────────────┤
            │ .bss .data │ globals     (S5)
            │  .text     │ code        (everything you've read)
  0x400000  └────────────┘ low
```

Live: `cat /proc/$(pgrep licensed)/maps` (or gdb `info proc mappings`). Real
segments, real addresses, mapped libraries.

**Syscalls, the just-enough version:**

> "Your code runs in *user mode*. It cannot touch the disk, the network, or the
> screen directly — only the kernel can. When your program needs any of that, it
> makes a **syscall**: it puts a number in `rax`, arguments in the usual
> registers, and executes `syscall`, which traps into the kernel. That's the
> whole user/kernel boundary. `printf` isn't magic — it eventually calls
> `write(1, ...)`, syscall number 1. libc is a library of convenient wrappers
> around these traps."

**ASLR in one minute:** "addresses are randomised each run so attackers can't
predict them — which is why your stack address changed between runs. For
debugging, gdb disables it by default so your life is reproducible. Know it's
there; S4's return-address trick is much harder *because* of it."

### A2 — How a breakpoint actually works (11 min)

The demystification that makes debuggers stop being magic:

> "How does gdb stop your program at exactly line 40? It **overwrites the byte**
> at that address with `0xCC` — the `int3` instruction, a one-byte software
> interrupt. When the CPU hits it, it traps to the kernel, which tells gdb. gdb
> then puts the *original* byte back, so you can inspect and continue as if
> nothing happened."

Show it live: `x/1bx $pc` before and after setting a breakpoint — the byte is
`0xCC`. Audible reaction guaranteed.

> "This matters for two reasons. One: a program can *detect* debugging by checking
> its own bytes for `0xCC` — that's an anti-debug trick you'll meet in S9. Two:
> now you understand a **hardware** watchpoint is different — the CPU watches an
> address and traps on *access*, no byte patching, which is how you catch 'who
> the hell is writing to this variable?'"

The gdb toolkit, off card #4, each with a one-line "use it when":
`break`/`tbreak`, conditional `break … if x==5`, `watch`/`rwatch`, `finish`,
`x`, `info registers`, and gdb scripting (`commands`, Python).

### A3 — strace, ltrace, and patching as experiment (12 min)

**Observe the boundaries, live on `phone_home`:**

```bash
strace -f ./phone_home     # every syscall: open, connect, write, read
ltrace ./phone_home        # every library call: strcmp, malloc, getenv
```

> "Before you read a single instruction, `strace` tells you if it opens a file,
> talks to the network, reads an environment variable. Thirty seconds of `strace`
> often beats an hour of static reading for the question 'what does this thing
> even touch?' This is triage — a lot more in S9."

**Patching, framed correctly:**

```
je  → jne     (flip the branch: 0x74 ↔ 0x75)
jcc → nop     (delete the branch: 0x90 padding)
function → ret   (stub it out: 0xc3)
```

> "You can flip a `je` to `jne` and make the licence check pass. You'll do it in
> ten minutes and it feels like winning. It is **not** winning. It's an
> experiment: 'I hypothesise *this* branch is the check.' If flipping it works,
> your hypothesis was right. If the program then crashes three functions later,
> you learned the check has a second half. A patch is a question you ask the
> program, not a trophy."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: break, watch, understand (40 min)

Full spec: [`labs/s07-lab.md`](../labs/s07-lab.md).

- **Core** — break on the comparison in `licensed`, read both operands, and
  report what it's comparing your input *against*. (Not "make it say valid" —
  *understand* the check.)
- **Stretch** — set a watchpoint on the variable holding the parsed key; report
  every place it's written and by what.
- **Boss** — make `licensed` accept a key by *understanding the transform*, then
  hand-computing a valid key — **no patching allowed.** Then, separately, achieve
  the same by patching, and write one paragraph on why the patch is the inferior
  solution here. (Explain-back.)

The Boss framing is deliberate: patching is the easy win, and the tier that bans
it is the one that teaches the most. A student who can only patch has not
understood the check.

---

## 1:50 — Teach B: live demo — the two ways to win (25 min)

**Target:** AURA-7's `auractl` licence check. Payoff of the S6 discovery that the
real check is inlined, not in the decoy.

**Way 1 — the cheap win (6 min).** Break on the inlined comparison, flip the flag
in gdb, program prints "Valid".

> "Done. Licensed. And I have learned almost nothing. I don't know what a valid
> key *is*, I couldn't make another one, and if there's a second check I've just
> walked into it blind."

**Way 2 — the real win (13 min).** Do it properly, narrating hypotheses, wrong
turns kept in:

1. Break on the comparison. Read *both* operands. One is my input; the other is
   computed. Where did the computed one come from?
2. Watchpoint on the computed value. Run. It's written after a loop over my
   input. **Scripted wrong turn:** "looks like a checksum, probably just adds the
   bytes" — check by feeding `AAAA` and reading the accumulator — nope, it's not
   a plain sum, there's a shift and an xor each round. Correct the hypothesis.
3. Recognise the *shape*: rolling transform, byte in, shift-xor-accumulate. (Full
   identification is S9 — today we just characterise it.)
4. State what a valid key must satisfy.

**Way 3 — patch on disk (6 min).** Take the cheap win and make it permanent:

```bash
objdump -d auractl | grep -A2 <cmp addr>       # find the je, note its file offset
# edit the byte 0x74 → 0x75 with a hex editor / python
python3 -c "b=open('auractl','rb+'); b.seek(0xADDR); b.write(b'\x75'); b.close()"
./auractl ...                                   # verify it now accepts anything
```

> "Now it's patched on disk, permanently, no debugger. That's a real technique —
> it's how you make a modified binary. But notice I only trust it because I first
> *understood* the check in Way 2. Patching something you don't understand is how
> you ship a broken crack."

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: script the observation (30 min)

Students write a **gdb Python script** that logs every call to the transform
function with its input byte and the running accumulator — turning a manual watch
into an automated trace.

- **Core:** a breakpoint script printing the accumulator each iteration.
- **Stretch:** log input byte + accumulator as a table; spot the per-round op.
- This directly sets up S9's full algorithm identification.

Seed the drill: **"ask a model to write this gdb script. Run its version. Keep
it."**

---

## 2:55 — Falsification Drill + close (5 min)

Today's drill is special: the artifact under test is **AI-generated tooling**, not
an AI analysis. This is the most realistic use of AI in RE — "write me the
script" — and its most common failure.

**The claim.** The model's gdb script "logs the accumulator each iteration."

1. *State it.* It should print N lines for N input bytes.
2. *What would falsify it?* — run it on a known 4-byte input; it should print 4
   accumulator values. Count the lines.
3. *Observe.* It prints once, or with wrong syntax (`$rax` where the value is in a
   local; or `commands` without `end`; or reads the accumulator *before* the
   round updates it — off by one, again). Something is subtly wrong.
4. *Verdict.* **Wrong — subtly.** Reason: the model produced *plausible gdb
   Python* — right shape, wrong detail (a register name, a hook point, an
   off-by-one in when it samples). Fixable in ten seconds **if you understand
   what the script should do**, unfixable by re-prompting a model that has the
   same blind spot. Record it.

> "This is the AI failure mode you'll hit most in real work. Not 'AI can't reverse
> engineer' — it's 'AI writes tooling that's 90% right and the 10% is a wrong
> register name that makes every number a lie.' You fix it in seconds because you
> know where the value actually lives. Someone who doesn't re-prompts five times
> and ships the wrong trace."

**Cold-open reveal.** The right first breakpoint wasn't on the "Invalid" print —
it was on the *comparison*, before the decision, where both operands are still
live. Breaking after the decision tells you it failed; breaking on the decision
tells you *why*.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 7 | Model's gdb script logs the accumulator each iteration | ✗ Wrong (subtle) | Plausible gdb Python, wrong detail (register name / sample point / off-by-one). 90% right, 10% makes every value wrong. Fixed by knowing where the value lives, not by re-prompting |

---

## Lecturer notes

**`int3` is the wow moment — spend on it.** Seeing `0xCC` appear in their own
program's bytes is when the debugger stops being magic and becomes a mechanism.
It also pays off directly in S9's anti-debug segment.

**Patching euphoria.** Students will get high on flipping branches. Channel it
with the Boss tier's no-patching rule and Way 2 of the demo. The message all
session: patching is a great experiment and a poor understanding.

**ltrace may be absent or flaky on the image.** Verify beforehand; `strace -e
trace=...` covers most of it if ltrace is missing. Don't discover this live.

**ASLR confusion.** Someone's address won't match yours. Explain once: gdb
disables ASLR, bare execution doesn't. Move on; full treatment isn't needed here.

**Running long.** Cut Lab A Boss, then Way 3 (disk patch) of the demo — but keep
Way 1 vs Way 2, that contrast is the session. Protect the `int3` reveal.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-7)

- **Read:** *Practical Binary Analysis* ch. 8–9 (dynamic analysis), 30 min.
- **Do:** write a gdb Python script that logs every `malloc` size in some program;
  compare to `ltrace -e malloc`.
- **Crackme:** crackmes.one difficulty 3, a "keygen-me" — write an actual keygen,
  don't patch.
- **Self-check:** 5 questions, answers included.
