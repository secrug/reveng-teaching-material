# Reverse Engineering 101

**10 sessions × 3 hours · biweekly · x86-64 Linux · first-year CS · ungraded**

A reverse-engineering course for students who know C and nothing else about how a
computer actually runs their code. No operating systems course required — this
course teaches the OS concepts it needs, when it needs them.

---

## The thesis

> AI moved the bottleneck from *"can you read assembly"* to *"do you know what to
> ask, and can you tell when the answer is wrong."* Both are fundamentals.

An LLM will solve in twenty seconds a crackme a student has been fighting for
forty minutes. This is going to happen in Session 1, in the room, whether we plan
for it or not. The predictable student conclusion — *the fundamentals are
obsolete* — is wrong, but it is not stupid, and it cannot be argued away with
exhortation.

So the course does not ban AI and does not moralize about it. It makes AI's
failure modes **empirically visible**, every session, until "verify before you
trust" is a reflex instead of a slogan. By Session 10 the class owns a written,
evidence-backed map of where machine assistance succeeds and where it collapses
on binaries — a map they derived themselves.

A student who cannot read a stack frame cannot notice when a model invents one.
That is the entire argument, and the course is built to let students discover it
rather than be told it.

---

## What students can do at the end

1. Read x86-64 assembly fluently enough to reason about what a function does
   without a decompiler.
2. Reconstruct control flow, data structures and function signatures from
   compiled code.
3. Drive a debugger with intent — breakpoints, watchpoints, scripting, patching
   — as hypothesis tests rather than as flailing.
4. Navigate a stripped binary in Ghidra and know precisely which parts of the
   decompiler's output to distrust.
5. Explain how a program gets from source file to running process, including
   linking, loading and dynamic symbol resolution.
6. Triage an unfamiliar binary and decide *where to spend attention* — the skill
   that separates a reverse engineer from someone who knows assembly.
7. Recognise when they've met something specialised (a packer, an anti-debug
   trick, a custom VM) and look it up without panic.
8. Use AI as a hypothesis generator and verify its claims against evidence.

---

## How to teach this course

Read these in order:

| Document | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The pedagogy: session template, the anti-complacency doctrine, the prerequisite matrix, how the whole thing is wired together. **Read this first.** |
| [sessions/](sessions/) | Ten minute-by-minute session designs. Each is teachable cold. |
| [labs/](labs/) | Tiered lab specs (Core / Stretch / Boss) with solution outlines. |
| [binaries/BUILD-PLAN.md](binaries/BUILD-PLAN.md) | Every binary to build, its source sketch, compile flags, and the AI-hostile property deliberately engineered into it. |
| [infra/SETUP.md](infra/SETUP.md) | Docker image, the ARM-Mac problem and its three mitigation tiers, failure fallbacks. |
| [handouts/REFERENCE-CARDS.md](handouts/REFERENCE-CARDS.md) | Five printed one-pagers. These are what students keep. |
| [AI-SCOREBOARD.md](AI-SCOREBOARD.md) | The class-maintained record. Print it, put it on the wall, fill it in every session. |
| [RESOURCES.md](RESOURCES.md) | The optional "Get Good" home track, mapped session by session. |
| [sessions/s01-intro-script.md](sessions/s01-intro-script.md) | The full opening-lecture script: the "two futures, one foundation" argument for why fundamentals survive AI. Deliver this with the projector off. |
| [ctf/](ctf/) | The AURA-7 CTF suite — original, AI-resistant challenges for the team to train on and field in competitions (CTFd), with writeups and heavy labs. Start with [ctf/ARCHITECTURE.md](ctf/ARCHITECTURE.md). |

---

## The shape of a session

Three hours, one room, laptops open. Never more than 35 minutes of talking.

```
0:00  Warm-up / retrieval      15   bridges the two-week gap
0:15  Cold open + prediction   10   today's mystery, committed in writing
0:25  Teach A                  35   whiteboard + terminal
1:00  Break                    10
1:10  Lab A                    40   Core / Stretch / Boss
1:50  Teach B / live demo      25   lecturer solves aloud, dead ends included
2:15  Break                    10
2:25  Lab B                    30   applied to the course-long target
2:55  Falsification Drill      5    + scoreboard, cold-open reveal, close
```

Talk 60 · hands-on 70 · retrieval and reveal 30 · breaks 20.

---

## Three structural choices worth knowing about before you start

**The decompiler is withheld until Session 6.** Sessions 1–5 are `objdump`, `gdb`
and paper. Tell the students this on day one and tell them why: the decompiler
was the previous generation's AI, and engineers who only ever read its output
plateau. They get the power tool once they can work without it — and they spend
Session 6 hunting places it lies.

**There is one target across all ten sessions.** AURA-7, a wholly synthetic
embedded telemetry device. Each session peels one layer. With no grades to supply
pressure, visible cumulative progress is what brings students back in week 19.

**Homework is offered, never required.** Every session stands alone. The optional
track is for students who want to get good; the course does not collapse if
nobody touches it.

---

## Legal and ethical note

Every binary in this course is synthetic and supplied by the course. AURA-7 is
not a real product and resembles none. Session 10 covers the law properly —
jurisdiction, licence terms, responsible disclosure, and the difference between a
lab binary and someone else's production server — but the boundary applies from
Session 1: **students reverse the course's binaries, not other people's.**
