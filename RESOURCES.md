# Resources — the optional "Get Good" track

The course is ungraded, so this is **offered, not required.** Every session stands
alone without it. But reverse engineering is a skill, and skills need reps — this
is the ladder for students who want to actually get good, mapped session by
session so nobody has to guess what to do next.

Per session, four things: **one reading** (20–30 min), **one exercise**
(45–90 min), **one crackme** at the right difficulty, and a **5-question
self-check** (with answers — provided in the solutions repo so students can check
themselves).

---

## The core references (worth owning / bookmarking)

| Resource | What it's for | Cost |
|---|---|---|
| **CS:APP** (*Computer Systems: A Programmer's Perspective*), Bryant & O'Hallaron | The machine model, done properly. Chapters 1–3 and 7 are the backbone. | textbook |
| **RE for Beginners** (Yurichev) | Free, enormous, x86/ARM side by side. The reference for "how does X compile?" | free PDF |
| **Practical Binary Analysis** (Andriesse) | Dynamic analysis, instrumentation, the tooling mindset. S7–S9. | book |
| **The Ghidra Book** (Eagle & Nance) | The decompiler tool, in depth. S6. | book |
| **crackmes.one** | Graded-difficulty practice binaries. The main gym. | free |
| **microcorruption** | Browser-based, zero-setup embedded RE. Different ISA (MSP430) — a *feature*: it proves the concepts transfer. | free |
| **pwn.college** | Structured, ambitious, free. For students who catch the bug. | free |

**On difficulty labels:** crackmes.one difficulty is community-assigned and
noisy. The mappings below are starting points — steer individual students up or
down by what they can actually do, not by the number.

---

## Session 1 — Binaries & lossiness {#session-1}
- **Read:** CS:APP ch. 1 — the compilation pipeline and the memory hierarchy.
- **Do:** compile a program of your own at `-O0`/`-O2`/`-Os`; diff the asm; write
  down what vanished.
- **Crackme:** crackmes.one difficulty 1, any "strings"-solvable challenge — then
  find one where strings *doesn't* work and notice the difference.
- **Self-check:** what survives compilation? why can't a perfect decompiler exist?
  what's the difference between `file` and `xxd`?

## Session 2 — The machine {#session-2}
- **Read:** CS:APP §3.1–3.5 — data formats, moving data, arithmetic.
- **Do:** microcorruption tutorial + first two levels. Different ISA on purpose.
- **Crackme:** crackmes.one difficulty 1, "arithmetic" tag.
- **Self-check:** what does writing `eax` do to `rax`? `lea` vs `mov`? what does
  `[rbx+rcx*8]` tell you?

## Session 3 — Control flow {#session-3}
- **Read:** CS:APP §3.6 — control flow, the whole chapter section.
- **Do:** write a 10-case `switch`; compile `-O0`/`-O2`; find where it stops being
  a jump table and becomes an if-chain / binary search.
- **Crackme:** crackmes.one difficulty 1–2, "control flow" / "keygen-me".
- **Self-check:** why does `if (x>5)` compile to `jle`? signed vs unsigned jumps —
  what do they reveal? where can a decision hide with no branch?

## Session 4 — Stack & ABI {#session-4}
- **Read:** CS:APP §3.7 — procedures, the stack, the call mechanism.
- **Do:** write a 3-arg function; confirm the args land in `rdi`/`rsi`/`rdx` at
  `-O0` and `-O2`; find where each lives in each build.
- **Crackme:** crackmes.one difficulty 2, multi-function.
- **Self-check:** which register holds arg 3? how do you recover arity from a
  stripped function? what is at `[rbp+8]`?

## Session 5 — Data & types {#session-5}
- **Read:** CS:APP §3.8–3.9 — arrays, structs, alignment.
- **Do:** define three structs with deliberate padding; predict each `sizeof`;
  verify; then read them back off the asm.
- **Crackme:** crackmes.one difficulty 2, a "serial" / structured-input challenge.
- **Self-check:** what does the `*scale` reveal? why is `sizeof` not the sum of
  fields? how do you tell an array access from a struct field?

## Session 6 — Tools & decompilers {#session-6}
- **Read:** *The Ghidra Book* ch. 1–5 (skim).
- **Do:** decompile a program you wrote yourself and find the *first* thing Ghidra
  gets wrong — powerful precisely because you know the ground truth.
- **Crackme:** crackmes.one difficulty 2–3 — solve with Ghidra, then verify the
  key claim in gdb.
- **Self-check:** name three decompiler failure modes. what is a cross-reference
  and why navigate by it? in what sense is the decompiler like an LLM?

## Session 7 — Dynamic analysis {#session-7}
- **Read:** *Practical Binary Analysis* ch. 8–9.
- **Do:** write a gdb Python script logging every `malloc` size in some program;
  compare against `ltrace -e malloc`.
- **Crackme:** crackmes.one difficulty 3, a "keygen-me" — write an actual keygen,
  do not patch.
- **Self-check:** how does a software breakpoint work? watchpoint vs breakpoint?
  when is patching the *wrong* answer?

## Session 8 — Linking & loading {#session-8}
- **Read:** CS:APP ch. 7 — linking, the definitive treatment.
- **Do:** build a program static and dynamic; compare sizes and `readelf -d`;
  break the dynamic one by moving a library.
- **Crackme:** crackmes.one difficulty 3 involving shared libraries, or a
  "solve with LD_PRELOAD" challenge.
- **Self-check:** segments vs sections — who reads each? trace a call through
  PLT/GOT. what does stripping *not* remove?

## Session 9 — Methodology {#session-9}
- **Read:** *Practical Binary Analysis* ch. 5–6; then skim one real crackme
  writeup or a published malware teardown — for the *method*, not the target.
- **Do:** full teardown of a difficulty-3/4 crackme, keeping a proper hypothesis
  log ([template](handouts/WORKSHEETS.md#the-re-notebook-all-sessions-the-one-habit-to-keep)).
  The log matters more than the solve.
- **Crackme:** crackmes.one difficulty 4, or a first pwn.college module.
- **Self-check:** the 5 triage steps? the hypothesis loop? how do you recognise
  AES / base64 / a state machine? what do you do when you hit a custom VM?

## Session 10 — Capstone & beyond {#session-10}
- **Do:** enter one CTF, rev or pwn category. Any. The point is the arena.
- **Read:** pick your field (vuln research / malware / firmware / interop) and
  read one real writeup in it.
- **Keep:** the hypothesis-log habit. Forever.
- **Self-check:** what does AI do well on binaries? what does it reliably fail at?
  how do you *know* when it's wrong?

---

## The C-and-memory safety valve (only if the cohort turns out uneven)

The course assumes solid C. If a given cohort proves shakier than expected, this
optional pre-track catches them up without slowing the lectures — **no session
depends on it.**

- Pointers and pointer arithmetic; arrays decaying to pointers.
- `struct` layout and why `sizeof` ≠ sum of fields (a preview of S5).
- The stack vs the heap; `malloc`/`free`; what a dangling pointer is.
- Reading: CS:APP ch. 3 intro; or any solid "pointers in C" primer.

Offer it after Session 1 if you see students struggling with the memory model in
the S1 lab. It is a bridge, not a prerequisite.

---

## For the ambitious (beyond the course)

- **CTF teams** — the fastest way to get good is a team that does rev/pwn.
- **Read real writeups** — the CTF and security community publishes teardowns
  constantly; reading them trains pattern-recognition faster than solo grinding.
- **Other tools** — IDA (Free tier), Binary Ninja (cheap for students), radare2 /
  rizin, angr (symbolic execution). The course teaches Ghidra as one instrument
  for a method; the method transfers to all of them.
- **Other architectures** — you learned x86-64 and glimpsed ARM64. The concepts
  are the invariant; each new ISA is just new spelling. That transfer *is* the
  skill.
