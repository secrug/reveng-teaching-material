# AURA-7 CTF Suite — Architecture

A suite of original CTF challenges for the team to train on and to field in
external competitions, hosted on CTFd. The defining constraint: **challenges that
AI is not trained on** — resistant to pure recall and to naive automated solving,
while remaining fair and solvable for a skilled human, ideally a human *guiding*
an AI.

This document is the design. Implementation follows it, challenge by challenge.

> **Status:** research + architecture complete; one reference challenge
> (`rev/signal-lock`) built end-to-end to validate the pipeline. The rest are
> specified here and built on approval of this design.

---

## 1. What already exists (so "novel" means something)

From a scan of the current landscape (sources at the end):

**How AI does on CTFs today.** On public benchmarks (InterCode-CTF, NYU-CTF,
CyberSecEval 2, and the newer CTFusion), plain LLMs solve **well under half** of
challenges at release. With agent scaffolding — tools, chain-of-thought,
multi-attempt, execution feedback — pass rates jump dramatically **on
challenges that resemble their training data**. Two failure clusters persist:
**memory-corruption pwn** (buffer/heap exploitation needed architectural tricks to
move at all) and **genuinely novel constructs** (anything not well-represented in
public writeups). This matches the lecturer's field observation exactly: the tools
shine on the familiar and stall on the new.

**The stock RE archetypes** (what every model has seen thousands of times, and
therefore what we must *not* ship unmodified):

- native crackmes / licence checks (trace to `strcmp`, flip a branch);
- custom encodings — plain XOR, standard base-N, byte shuffles;
- **custom VMs** — but the *textbook* stack-based and register-based kinds are a
  well-known genre; models recognise the interpreter loop and map opcodes fast;
- managed-runtime rev (.NET, JVM, Android, compiled Python) — high recall;
- standard anti-debug (`ptrace(TRACEME)`, `IsDebuggerPresent`, timing).

**Anti-automation is a real, published discipline.** Against symbolic-execution
solvers (angr), the effective techniques are **one-way/hash opaque predicates**
(constraints a solver can't invert) and **path-explosion predicates** (flood the
solver with bogus branches). We use these deliberately, and *sparingly*, only
where the lesson is "understanding beats brute force."

**Conclusion.** Novelty cannot come from the *category* (they're all known). It
must come from four levers, below.

---

## 2. The novelty engine — how we actually make these AI-resistant

Four levers, applied per challenge. Each challenge's writeup states which it uses
and **which specific AI failure mode it targets** — the challenges are the
course's AI Scoreboard, weaponised.

### Lever 1 — Original artifacts, so recall fails
No challenge here has a public writeup, because none existed before. An LLM's
biggest edge — "I have seen this exact problem" — is removed by construction. This
alone defeats pure pattern-matching; it does not defeat reasoning, which is the
point (see §3).

### Lever 2 — Semantics that must be *inferred*, not *recalled*
The flagship move: a machine model the solver has to build from evidence because
it does not match any textbook. We do **not** ship a stack-VM. We ship an
**unusual computer** — a transport-triggered architecture, a one-instruction-set
computer variant, a belt machine — real CS concepts, rare in CTFs, with no
familiar interpreter-loop silhouette for a model to latch onto. The solver
reconstructs the ISA the way S9 taught: from behaviour, not from memory. An AI
*can* do this, but only by genuine reasoning, and it is exactly where guided
human+AI beats unguided AI.

### Lever 3 — Per-instance secrets, so answers don't transfer
Flags and key constants are derived, at deploy time, from a per-instance seed
(per-team where CTFd supports it, else per-event). Consequence: there is no
constant to memorise or leak; the only durable solution is a **reusable method**.
This also blunts flag-sharing and makes "ask the model for the answer" useless
even if a prior solver posted one.

### Lever 4 — Traps calibrated to the model's priors
Decoys and near-misses engineered to trigger the statistical prior and send it
confidently wrong — the same mechanism as the course's AI-hostile artifacts, at
competition strength:
- a cipher that is AES/TEA-shaped with **two swapped S-box entries** (the model
  says "it's AES" and forges wrong keys);
- a function named `verify_flag` that is a decoy; the real check is inlined;
- a loop bound that is `<=` where the idiom is `<`;
- self-modifying code so the **static** view a decompiler/LLM reads is not the
  code that runs.

### The honesty caveat (state this to the team, too)
We do **not** claim "no AI can solve these." A well-resourced, human-guided agent
should be *able* to — that is the thesis, not a bug. What we guarantee is:
recall and naive automation don't shortcut them; they reward method and
creativity; and a human who understands the fundamentals, using AI as an
instrument, is the intended winning configuration. And, exactly as the course
demands: **re-verify against a current model before each deployment** (§7). A
challenge that a model now one-shots has not failed us — it has told us the
boundary moved, which is a finding to teach from.

---

## 3. Two threat models

Every challenge is designed against both, and says which it prioritises.

| | **TM-A: the LLM/agent** | **TM-B: the automated solver** (angr/concolic, unicorn brute force) |
|---|---|---|
| Strength | recall, code reading, breadth, tooling glue | exhaustive path search, constraint solving, tireless |
| Weakness | novelty, exactness (offsets/padding), intent, long chains | path explosion, one-way constraints, huge state, interaction |
| Our lever | 1, 2, 4 (original, inferred semantics, priors) | one-way/path-explosion predicates, per-instance interaction |

Most REV challenges target TM-A. `crypto/one-way-gate` and the VM challenges also
target TM-B. PWN challenges are naturally hard for both today (per the benchmark
reality) and lean on per-instance remote state.

---

## 4. Theme and continuity

All challenges live in the **AURA-7** universe (the fictional smart-industrial
telemetry rig from the course), so a team that took the course arrives with
narrative context and a mental map. But **every challenge is standalone-playable**
— nothing requires having solved another (except where a challenge explicitly
lists a prerequisite, used only in the Labs). External CTF players need no AURA-7
knowledge; the theme is flavour, never a gate.

The device gives us a plausible, generous attack surface:

```
  aura-fw.bin      firmware blob: header, sections, checksum, embedded ASP bytecode
  aurad            the daemon: length-prefixed binary protocol over TCP/unix socket
  auractl          the CLI client: config parsing, licence check
  ASP              the "AURA Signal Processor" — a transport-triggered coprocessor
                   running bytecode (our custom-ISA novelty engine)
  licence system   a custom block cipher (AES-shaped, subtly wrong)
```

---

## 5. The catalogue

Point values assume CTFd **dynamic scoring** (value decays with solve count).
"AI target" = the primary AI failure mode the challenge is built to expose (ties
to the course scoreboard). Course-skill column maps back to the ten sessions so
the team knows what to review.

### REV track

| ID | Name | Tier / pts | The idea | Novelty levers | AI target | Course skill |
|---|---|---|---|---|---|---|
| rev/warmup-decoder | Signal Primer | Intro / 100 | position-dependent byte transform vs embedded target | 1 | *(calibration — AI should solve this; teaches the team what AI is good at)* | S1–S3 |
| rev/padded-struct | Wire Format | Easy / 150 | flag validated against a packed struct; padding + endianness traps | 1, 4 | struct padding offsets (S5 failure) | S5, S8 |
| **rev/signal-lock** | **Signal Lock** | **Medium / 250** | **transport-triggered mini-VM crackme — the novelty engine, small.** *(REFERENCE CHALLENGE — built)* | 1, 2, 3 | inferred semantics; no interpreter-loop silhouette to recall | S2, S3, S9 |
| rev/mirror | Hall of Mirrors | Medium / 300 | self-modifying code: real check decrypted+run at runtime; static view is garbage | 1, 2, 4 | static decompilation (what an LLM reads) ≠ runtime code | S6, S7 |
| rev/asp-coprocessor | The Coprocessor | Hard / 450 | full ASP: recover the transport-triggered ISA, then the bytecode flag-checker | 1, 2, 3 | novel machine model; long inference chain | S2, S3, S9 |

### PWN track

| ID | Name | Tier / pts | The idea | Novelty levers | AI target | Course skill |
|---|---|---|---|---|---|---|
| pwn/aurad-parser | Overrun | Medium / 250 | stack overflow in the length-prefixed protocol parser; no canary/PIE | 1, 3 | memory-corruption (benchmark-hard) + remote per-instance | S4, S7 |
| pwn/telemetry-heap | Ring Zero | Hard / 400 | UAF / overflow into a function-pointer table in a telemetry ring buffer | 1, 3 | modern heap; multi-step | S5, S7 |
| pwn/asp-escape | Breakout | Insane / 550 | sandbox escape: OOB in the ASP VM's memory array → native write → RCE | 1, 2, 3 | rev+pwn chain on a *custom* VM (no precedent) | S4, S7, S9 |

### CRYPTO-RE crossover

| ID | Name | Tier / pts | The idea | Novelty levers | AI target | Course skill |
|---|---|---|---|---|---|---|
| crypto/aura-license | Counterfeit | Medium / 300 | AES/TEA-shaped licence cipher with a subtly modified S-box/schedule; recover + forge | 1, 4 | "it's AES" — right genre, wrong specifics (S9 failure) | S5, S9 |
| crypto/one-way-gate | Brick Wall | Hard / 400 | flag gated behind one-way + path-explosion opaque predicates; angr chokes | 1, 4 (TM-B) | defeats "throw angr at it"; forces understanding | S3, S9 |

### MISC / hardware-flavoured

| ID | Name | Tier / pts | The idea | Novelty levers | AI target | Course skill |
|---|---|---|---|---|---|---|
| misc/firmware-triage | Teardown | Easy / 200 | parse `aura-fw.bin`: header, checksum, section table, extract embedded ASP bytecode | 1 | exact offsets / format inference | S1, S8 |
| misc/blind-protocol | Cold Call | Medium / 300 | only a live service + a pcap; reverse the wire protocol from traffic, no binary | 1, 3 (TM-A/B) | black-box; no code to read at all | S8, S9 |

**Twelve challenges, laddered Intro→Insane, across four tracks.** The intro-tier
`warmup-decoder` is deliberately AI-solvable — it calibrates the team on what the
machine *is* good at, which is as important as showing where it fails.

### Heavy labs / big projects (multi-day, not single flags)

| ID | Name | Shape | What it builds |
|---|---|---|---|
| labs/own-the-rig | **Own the Rig** | capstone chain: triage firmware → recover licence → forge → speak protocol → parser bug → RCE → escape ASP VM → final flag. Chains 6+ challenges. | the full professional workflow end-to-end; weeks of work |
| labs/build-a-breaker | **Build a Breaker** | meta-lab: each student *builds* a challenge that defeats a named AI agent, documents the failure mode, then teams swap and solve. | novelty engineering — the intro's promise, made real |
| labs/blind-rig | **The Blind Rig** | black-box: a running rig, no binaries, only network access + captures. Reverse and exploit purely from interaction. | the hardest real-world mode; where AI is weakest |

---

## 6. CTFd packaging (how it ships)

Standard **ctfcli** layout, one directory per challenge, deployable with
`ctf challenge install` / `sync` and `ctf challenge deploy`.

```
ctf/challenges/<track>-<name>/
  challenge.yml         # the CTFd spec (schema below)
  README.md             # player-facing prompt (mirrors description)
  src/                  # full source (C, Python, build scripts)
  Dockerfile            # for networked pwn/misc; static rev builds a dist artifact
  docker-compose.yml    # for services (aurad, etc.)
  dist/                 # exactly what the player downloads (built artifact only)
  solution/
    WRITEUP.md          # the full writeup (also referenced by challenge.yml `solution:`)
    solve.py            # reference solver — MUST run green in CI
  healthcheck.sh        # scripted solve for CTFd health monitoring
  make_flag.py          # per-instance flag/secret derivation from a deploy seed
```

**`challenge.yml`** uses the verified CTFd schema. Reference skeleton:

```yaml
name: "Signal Lock"
author: "AURA-7 course team"
category: rev
description: |
  The AURA-7 rig won't unlock without the right signal. We pulled the
  verifier off the board. Find the key it wants.
  Download: {file}
attribution: "Original challenge — AURA-7 course suite"
value: 250
type: dynamic            # decaying score
extra:
  initial: 250
  decay: 30
  minimum: 100
version: "0.1"
image: null              # static rev: no service. (pwn/misc set image + host)
protocol: null
host: null
state: hidden
solution: solution/WRITEUP.md   # uploaded as a hidden CTFd solution
attempts: 0              # unlimited
logic: any
flags:
  - type: static
    content: "AURA{...}"        # per-instance: generated by make_flag.py at deploy
    data: case_sensitive
topics: [transport-triggered-vm, custom-isa, dynamic-analysis]  # admin-only
tags: [rev]                                                     # public
files:
  - dist/signal-lock             # ONLY the built artifact ships
hints:
  - content: "It is a computer. It just isn't the computer you're expecting."
    cost: 25
  - content: "Watch what happens when a value is written to address 0xE0..0xEF. Nothing is 'moved' for free."
    cost: 50
```

**Key operational rules:**
- **Ship only `dist/`.** Never ship source, symbols you didn't intend, the
  writeup, or `make_flag.py`. A `dist-check` script asserts the built artifact
  contains no accidental leak (no `.comment` giveaways, no debug strings, flag not
  present in plaintext).
- **Dynamic scoring** everywhere so early solvers are rewarded and easy challenges
  deflate.
- **Per-instance flags** via `make_flag.py`, seeded from a deploy env var; the
  `flags:` entry is templated at sync time. For pwn/misc the flag lives only on
  the server (`/flag`, root-owned, readable post-exploit).
- **Healthchecks** are the reference `solve.py`, wired to `healthcheck.sh`, so
  CTFd tells you the moment a challenge breaks mid-competition.
- **Hints cost points** and ladder — the first nudges toward the *category* of
  surprise, later ones toward mechanics, none give the answer.

---

## 7. Operational discipline (borrowed from the course, non-negotiable)

1. **CI proves solvability.** Every challenge's `solve.py` runs in CI against the
   freshly built artifact/service and must recover the flag. A challenge whose own
   solver fails does not ship. This is the CTF analogue of the course's
   `make verify`.
2. **Re-verify against a current AI before each deployment.** Run the challenge
   through a current agent (unguided) and record the outcome, exactly like the
   course's Falsification Drill. Expected: it stalls on the novel ones and clears
   `warmup-decoder`. If a "hard" one now falls to unguided AI, that is data — bump
   its difficulty (add a lever) or re-tier it, and tell the team where the wall
   moved. **Never fake resistance.**
3. **Per-instance where it matters.** Any challenge whose flag could leak uses
   `make_flag.py`. Test the derivation is deterministic per seed and distinct
   across seeds.
4. **Difficulty is measured, not asserted.** Track first-blood time and solve
   count per challenge across practice sessions; re-tier from data.

---

## 8. Build order

Dependencies first (they're reused), then difficulty-ascending within a track so
each build validates tooling before the expensive ones.

1. **`common/`** — the ASP virtual machine (shared by `signal-lock`,
   `asp-coprocessor`, `asp-escape`, and the firmware blob) and the licence cipher
   (shared by `aura-license`, `own-the-rig`). ✅ `asp_reference.py` built + validated.
2. **REV track (all 5)** — ✅ **built end-to-end**: `warmup-decoder`,
   `padded-struct`, `signal-lock`, `mirror`, `asp-coprocessor`. Each has source
   generator, `challenge.yml`, Dockerfile, healthcheck, writeup, and a verified
   reference solver; validated by `common/check_rev_track.py`.
3. **CRYPTO (both)** — ✅ **built end-to-end**: `aura-license` (ALC-64, an
   original 16-round Feistel with a custom S-box and LCG key schedule — a real
   keygen-me) and `one-way-gate` (one-way + path-explosion opaque predicates).
   Validated by `common/check_crypto_track.py`.
4. **MISC (both)** — ✅ **built end-to-end**: `firmware-triage` (a real
   `aura-fw.bin` with a section table, checksum trailer and a decoy flag — closes
   the S1 "length doesn't match filesize" thread) and `blind-protocol` (a live
   Dockerised service + a real libpcap capture; solved over a socket, and its
   endianness trap proven to reject replay and naive XOR).
   Validated by `common/check_misc_track.py` + each `healthcheck.sh`.
5. **PWN (all 3)** — ✅ **built, design-complete**: `aurad-parser` (signed-length
   overflow → ret2win), `telemetry-heap` (tcache UAF → fptr hijack), `asp-escape`
   (ASP VM OOB write → trap-pointer hijack; chains rev+pwn). Vulnerable source +
   reference exploit + writeup + reference Dockerfile; exploit logic validated by
   `common/check_pwn_track.py`, full exploit by each `healthcheck.sh` on a Linux
   host. Production jail/limits deferred to ops — see `challenges/HOSTING.md`.
6. LABS: `own-the-rig` (chains the above), then `build-a-breaker`, `blind-rig`.
   ← **next**

**Build environment note:** these are Linux x86-64 ELF challenges and networked
services. They build and get verified in the course's Linux toolchain / Docker
(`infra/SETUP.md`), not on the authoring machine. Every challenge ships its own
`Dockerfile`/build script so builds are reproducible and CI-checkable. Challenge
*logic* (transforms, ciphers, VM semantics) is validated in Python first so the
math is proven correct before it's committed to C.

---

## Sources

- [InterCode-CTF benchmark](https://www.emergentmind.com/topics/intercode-ctf) ·
  [CTFusion (arXiv)](https://arxiv.org/html/2605.11504v1) ·
  [Autonomous LLM Agents & CTFs: A Second Look (arXiv)](https://arxiv.org/html/2605.21497v1) ·
  [Hacking CTFs with Plain Agents (arXiv)](https://arxiv.org/pdf/2412.02776)
- RE archetypes: [Reverse Engineering CTF Guide (ctfhelper)](https://ctfhelper.com/guides/rev-ctf) ·
  [Solving a VM-based CrackMe (0ffset)](https://www.0ffset.net/reverse-engineering/solving-a-vm-based-crackme/) ·
  [gynvael: VM-based challenge](https://gynvael.coldwind.pl/?lang=en&id=763)
- Anti-symbolic-execution: [Novel Opaque Predicate Techniques to Counter Dynamic Symbolic Execution (CMC 2025)](https://www.techscience.com/cmc/v84n1/61718/html) ·
  [Code Obfuscation Against Symbolic Execution (Banescu, TUM)](https://mediatum.ub.tum.de/doc/1343173/1343173.pdf)
- Packaging: [CTFd ctfcli challenges](https://docs.ctfd.io/docs/management/ctfcli/challenges/) ·
  [challenge.yml example spec](https://github.com/CTFd/ctfcli/blob/master/ctfcli/spec/challenge-example.yml)
