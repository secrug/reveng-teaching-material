# Course Architecture

How the ten sessions are wired together, and why each choice was made. Read this
before teaching any session.

---

## 1. The problem this design solves

A first-year cohort with solid C and no OS course needs two things:

1. **Foundations internalised deeply** — assembly, calling conventions, memory,
   stack and heap behaviour, pointers, control flow, data structures, binary
   formats, linking and loading, debugging. Reasoned about *without* assistance.
2. **A working repertoire** — tracing data flow, recognising loops and switch
   tables, reconstructing structs, spotting compiler idioms, following indirect
   calls, breakpoint strategy, patching branches, finding cross-references,
   telling code from data. Enough exposure to *recognise when a technique
   applies*.

Specialised material (exotic anti-debug, custom VMs, unusual allocators, obscure
crypto) is explicitly **not** memorised. It appears once, in Session 9, as a
category with pointers. The message is stated plainly: nobody memorises these;
you learn to recognise the smell and then you go and read.

The complication is that all of this now sits next to a machine that can do a
substantial share of the mechanical work. The course has to teach the
fundamentals *while* a tool exists that appears to make them unnecessary.

---

## 2. Why fundamentals survive AI — the argument the course makes

Four claims, each demonstrated rather than asserted:

**Compilation is many-to-one, so RE is inference.** Many source programs compile
to the same machine code; information is genuinely destroyed. Recovering intent
is inference under uncertainty, not decryption. Inference needs priors, and
priors are fundamentals. *(Demonstrated S1.)*

**A generator is not a verifier.** A decompiler and an LLM are the same species
of thing: plausible-output generators. Both are useful. Neither establishes
truth. Only evidence does — a register value, a memory dump, a breakpoint that
fires. Producing that evidence requires knowing where to put the breakpoint.
*(Demonstrated S6, practised every session.)*

**Fluency is not correctness.** Model output is uniformly confident. The error
rate is not uniform — it spikes exactly where the binary departs from the
statistical prior. Students cannot detect that spike without a prior of their
own. *(Demonstrated by the AI-hostile artifacts, every session.)*

**Attention allocation is the real job.** On any binary above toy size, the work
is not *reading* code, it is deciding **which 2% of the code to read**. Nothing
delegates that, because it depends on the goal. *(Demonstrated S9, raced S10.)*

---

## 3. The anti-complacency doctrine

Six mechanisms, in every session. These are the structural answer to "students
stop caring once they see AI solve it."

### M1 — Predict-then-reveal
Students write a prediction before any tool runs. A written commitment cannot be
retroactively outsourced, and being wrong *on paper* is what makes the
explanation land. The cold open poses the question at 0:15; the answer is
revealed at 2:55.

### M2 — The Falsification Drill (every session, ~15 min)
An LLM produces an analysis of the session's artifact. Students must produce
**evidence** that confirms or refutes one specific claim in it — a register
value, a memory dump, a breakpoint hit, a byte at an offset. Not an opinion, not
a second model's opinion. Evidence.

The drill has a fixed script:

1. State the claim in one sentence, with its offset or symbol.
2. Name the observation that would falsify it.
3. Make the observation.
4. Record the verdict on the scoreboard, with the reason.

Step 2 is the whole exercise. A student who cannot name a falsifying observation
has not understood the claim well enough to accept it either.

### M3 — AI-hostile artifacts (at least one per session)
Binaries engineered so the statistical prior misleads. The catalogue lives in
[binaries/BUILD-PLAN.md](binaries/BUILD-PLAN.md); each entry documents the
property and the failure it is designed to provoke, so the drill **fires
reliably** rather than being hoped for. Examples: a single flipped comparison
byte, a hand-written non-standard calling convention, a struct whose alignment
holes are invisible in source, a function named `check_license` that does
nothing while the real check is inlined elsewhere.

One rule for the lecturer: **never announce which artifact is the hostile one.**
The point is the discipline of always verifying, not the sport of finding the
planted bug.

### M4 — No-tools segments
Hand-executing instructions, hand-decoding bytes, drawing stack frames in marker
on a whiteboard. Analog by design. These also break up three hours of screen
time, which matters more than it sounds.

### M5 — The AI Scoreboard
A class-maintained record of every drill: the claim, the verdict, and **the
reason for the failure**. The reason column is the valuable one — it is where
"AI is sometimes wrong" becomes "AI systematically fails on alignment padding,
exact offsets, flag semantics, and anything it has not seen a thousand examples
of." Reviewed as a body of evidence in S10.

### M6 — Explain-back
Boss-tier lab tasks require explaining the mechanism to a neighbour with notes
closed. Cheap, and it exposes the difference between having an answer and
understanding it.

---

## 4. Handling the moment it happens

It will happen in Session 1: a student solves the cold open with a model in
twenty seconds and says so, loudly. **This is a gift. Do not defend against it.**

The scripted response:

> "Good — do it again on this one." *(hand them the hostile variant)*
>
> "Now: is it right? Not does it sound right. How would you know?"

Then let them work at it in front of everyone. Either they produce evidence — in
which case they have just demonstrated the course's method to the room better
than the lecturer could — or they cannot, which is the more common outcome and
makes the point permanently.

What never works: telling students AI is unreliable, banning it, or setting tasks
it cannot do and pretending that is the normal case. The course's credibility
depends on being visibly honest about what the machine is good at. Sessions 6 and
10 both include explicit accounting of where AI genuinely outperforms a
first-year student, because it does, and pretending otherwise loses the room.

---

## 5. Why the decompiler is withheld until Session 6

Sessions 1–5 are `objdump`, `gdb` and paper.

Stated to students on day one, with the reason: the decompiler was the previous
generation's AI, and engineers who only ever read its output plateau. The failure
mode is identical — fluent plausible text, no ground truth, and no way to detect
the gap without the underlying skill.

This is not asceticism. It is the course's argument enacted on the students
themselves before it is made about AI, so that when Session 6 draws the parallel
the students have already lived both halves. A student who spent five sessions
reading assembly and then meets the decompiler understands viscerally what it is
doing *for* them, and therefore what it might be doing *to* them.

Practical consequence: the S1–S5 binaries must be small. A 40-line function is a
reasonable ceiling without a decompiler; a 400-line one is cruelty. The build
plan respects this.

---

## 6. The course-long target: AURA-7

A wholly synthetic embedded telemetry device. Not a real product; resembles none.

| Component | What it is |
|---|---|
| `auractl` | CLI client. Config parsing, licence check, command encoding. |
| `aurad` | Daemon. Listens on a unix socket, speaks a small binary protocol. |
| `aura-fw.bin` | "Firmware" blob — a flat file with a header, sections and a checksum. |

Layers peeled, session by session:

| S | What the class learns about AURA-7 |
|---|---|
| 1 | It exists. What kind of files these are; what `strings` gives and what it hides. |
| 2 | — *(drills use minimal binaries; AURA-7 rests)* |
| 3 | The command dispatcher is a jump table. Enumerate the commands. |
| 4 | Signatures of the handler functions, recovered from register liveness. |
| 5 | The config struct, recovered in full and proven by generating a valid config. |
| 6 | A named, typed, annotated Ghidra map of `auractl`. |
| 7 | Watch it run. Break on the licence check. Patch it. Then explain what broke. |
| 8 | `LD_PRELOAD` the check without touching the binary. Follow PLT/GOT live. |
| 9 | The whole thing: licence algorithm and wire protocol, end to end. |
| 10 | A *variant* nobody has seen, used for the race. |

With no grades supplying pressure, visible cumulative progress on one artifact is
the primary reason students come back in week 19. Protect it: never skip the
AURA-7 segment, even when a session runs long. Cut Lab A's Boss tier instead.

---

## 7. Prerequisite matrix

Every technique used in a lab is taught in that session or earlier. No forward
references. `T` = taught, `U` = used again.

| Concept | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Binary formats (surface) | **T** | | | | | U | | U | U | U |
| Compilation is lossy | **T** | U | U | U | U | U | | | U | U |
| Registers / instruction semantics | | **T** | U | U | U | U | U | | U | U |
| Memory as flat bytes, endianness | | **T** | | U | U | | U | U | U | U |
| Flags and comparison | | **T** | U | | | | U | | U | U |
| Basic blocks / CFG | | | **T** | U | | U | U | | U | U |
| Compiler lowering idioms | | | **T** | U | U | U | | | U | U |
| Jump tables / indirect control | | | **T** | | | U | U | U | U | U |
| Stack mechanics | | | | **T** | U | U | U | | U | U |
| SysV ABI / calling convention | | | | **T** | U | U | U | U | U | U |
| Stack frames, locals | | | | **T** | U | U | U | | U | U |
| Pointers / addressing in asm | | *(T)* | | U | **T** | U | U | U | U | U |
| Struct / array layout, padding | | | | | **T** | U | U | | U | U |
| Static vs heap vs stack storage | | | | | **T** | U | U | U | U | U |
| Type recovery as inference | | | | | **T** | U | | | U | U |
| Disassembly theory, code vs data | | | | | | **T** | | U | U | U |
| Decompiler semantics + failures | | | | | | **T** | U | U | U | U |
| Cross-references, annotation | | | | | | **T** | U | U | U | U |
| Process model, syscalls | | | | | | | **T** | U | U | U |
| Breakpoints, watchpoints, scripting | | *(T)* | U | U | U | | **T** | U | U | U |
| Patching | | | | | | | **T** | U | U | U |
| ELF anatomy, sections, symbols | *(T)* | | | | | U | | **T** | U | U |
| Linking, relocation, PLT/GOT | | | | | | | | **T** | U | U |
| `LD_PRELOAD` / interposition | | | | | | | | **T** | U | U |
| Triage / attention allocation | | | | | | U | U | | **T** | U |
| Algorithm shape recognition | | | | | | | | | **T** | U |
| Obscure techniques (pointers only) | | | | | | | | | **T** | U |
| Law and ethics | *(T)* | | | | | | | | | **T** |

*(T)* = introduced at surface level only, formalised later.

**Two dependencies to watch.** `gdb` is used from S2 but not *taught properly*
until S7 — S2–S6 use a deliberately tiny command set (`break`, `run`, `si`,
`info registers`, `x`), all of which are on the reference card from session one.
And pointers appear in addressing modes in S2 before being treated as a data
concept in S5; S2 handles them purely mechanically (`[rax+rbx*8]` is arithmetic)
and says explicitly that the meaning comes later.

---

## 8. The session template, and how to adapt it

```
0:00  Warm-up / retrieval          15
0:15  Cold open + prediction       10
0:25  Teach A                      35
1:00  Break                        10
1:10  Lab A                        40
1:50  Teach B / live demo          25
2:15  Break                        10
2:25  Lab B                        30
2:55  Falsification Drill + close   5
```

**Warm-up (15).** Retrieval practice, not revision. Five questions or a short
"be the CPU" trace from last session. Students answer, *then* see the answer by
doing — never by being told. This is the entire mechanism bridging a two-week gap
with no homework, so do not cut it. It also absorbs latecomers gracefully.

**Cold open (10).** A binary on screen and a question. Every student writes a
prediction. Collect them or don't; the writing is what matters.

**Teach A (35).** The core concept. Terminal on screen, whiteboard beside it.
Maximum ~12 slides for the whole session, each a diagram, an asm listing or a
memory map. No bullet walls. If you find yourself reading a slide, the slide is
wrong.

**Lab A (40).** Three tiers. **Core** is the floor — everyone finishes it, and
the session's outcome is met by finishing it. **Stretch** is the expected landing
zone. **Boss** exists so the fastest student in the room never idles and never
has to be entertained. Circulate; do not sit down.

**Teach B / live demo (25).** The lecturer works a harder problem live, narrating
hypotheses. **Keep the wrong turns in.** Students have never seen an expert be
confused on purpose, and it is the single highest-value thing in the session: it
is the only direct evidence they get that being stuck is normal rather than
disqualifying. If the demo goes right first time, it is teaching the wrong lesson.

**Lab B (30).** Applied to AURA-7. Continuity and visible progress.

**Falsification Drill + close (5).** The drill proper is seeded during Lab B —
students run the model while working — and the last five minutes are the verdict,
the scoreboard entry, the cold-open reveal, and the optional-track pointer.

**Adapting when you run long** (you will, in S4, S6 and S9). Cut in this order:
Boss tier → Teach B's second example → Lab A's third task. **Never cut**: the
warm-up, the AURA-7 segment, the cold-open reveal, or the scoreboard entry. Those
four carry the course's structure across the two-week gaps.

---

## 9. Slides, boards and handouts

**Slides are a reference artifact, not the lecture.** ≈12 per session, each one a
diagram, listing or memory map. They exist so a student who missed the session
can reconstruct the shape of it, and so the lecturer has an anchor. They are not
the delivery mechanism. The delivery mechanism is a terminal and a whiteboard.

**The board carries the memory drawings.** Stack frames, struct layouts, address
spaces, PLT/GOT indirection — draw these live, in real time, growing as you step
the debugger. A pre-drawn diagram shows the result; drawing it live shows the
*process*, which is what students cannot get from a book.

**The handouts are what students keep.** Five printed one-pagers, issued as the
sessions need them. Print them. Physical cards get used during no-tools segments
in a way a PDF never does.

---

## 10. Retention without grades — the honest risk register

| Risk | Mitigation | Residual |
|---|---|---|
| Two-week forgetting gap | 15-min retrieval warm-up; strict self-containment; reference cards | Real but managed. Expect S2→S3 to be the worst gap; S3's warm-up is the longest for that reason. |
| Attendance decay by S5–S6 | AURA-7 cumulative progress; S6 is the "you've earned the power tool" payoff, deliberately placed at the sag point | Watch it. If attendance drops below half by S5, move the S6 Ghidra reveal earlier. |
| Fast/slow spread in one room | Three-tier labs; Boss tier genuinely hard; explain-back gives fast students a role | Manageable. |
| Students who skip the optional track | Nothing depends on it; every session self-contained | By design — but they will be slower in labs. Budget extra circulation time. |
| ARM Macs make S2/S4/S7 painful | Three mitigation tiers, see `infra/SETUP.md` | **The one to solve before S2, not during it.** |
| Live demo fails on the day | Every demo pre-recorded as an asciinema cast | Fully covered. |

---

## 11. Where this course deliberately stops

- **Not an exploitation course.** S4 overwrites a return address once, for ninety
  seconds, to show *why* memory layout matters. Where to go next is named; the
  course does not follow.
- **Not a malware course.** No live samples, no sandbox requirements, no
  containment burden. S10 describes the career path.
- **Not a tools course.** Ghidra is taught as an instrument for a method, not as
  a curriculum. IDA, Binary Ninja, radare2 and angr are named in S6 and S9 as
  things that exist.
- **Not a breadth tour of architectures.** x86-64 throughout, with a deliberate
  ten-minute ARM64 and PE contrast in S8 — enough to separate *the concept* from
  *this ISA's spelling*, not enough to claim coverage.
