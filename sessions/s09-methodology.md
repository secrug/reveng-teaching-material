# Session 9 — Working like a reverse engineer: methodology on a real target

**The one idea:** the skill isn't reading code — it's deciding *which* code to
read. Triage, hypothesis, evidence, record, repeat. Everything before this
session was equipment; this session is the craft. It is the most important
session in the course.

---

## Outcomes

1. Triage an unfamiliar binary and decide where to spend attention *first*.
2. Run the hypothesis loop — form → predict → test → record — explicitly.
3. Switch between static and dynamic analysis deliberately, for a reason.
4. Recognise common algorithm *shapes* by their constants and structure (crypto,
   base64, checksums, state machines, parsers).
5. Recognise — not defeat — the specialised categories (packing, anti-debug,
   VMs, obfuscation) and know they are lookup-time, not memorise-time.
6. Score a model's whole-algorithm claim against ground truth the class built.

---

## Prep checklist

- [ ] Full AURA-7 set staged; `s09/` pack with `shapes_zoo` (constant-recognition
      drill), `antidebug_demo` (ptrace self-attach), `packed_demo` (UPX'd)
- [ ] Reference card **#5 (RE methodology + shape catalogue)** printed — the
      keystone handout, issued today
- [ ] The standing boards from S1/S3/S4/S5: OPEN QUESTIONS and AURA-7 MAP. Bring
      them back up — today they get closed
- [ ] Casts: `s09-demo.cast` (the full 45-min AURA-7 reverse — the crown jewel)
- [ ] **This session runs long by design. Pre-commit your cuts.**

---

## 0:00 — Warm-up (15 min)

Rapid tool-choice drills — "what would you reach for?", not "what's the answer":

1. Unknown binary, first 30 seconds — name three commands. *(file, strings, strace)*
2. You want to know what a function is called that has no symbol. *(xrefs from a
   string or PLT call)*
3. "Who writes to this global?" — static or dynamic, which tool? *(watchpoint)*
4. A function returns a constant and nothing uses the result. *(decoy — S6)*
5. Stripped binary, but it calls `socket`/`bind` — how do you know? *(PLT/dynsym
   survives — S8)*

This warm-up is a dry run of triage itself. That's intentional.

---

## 0:15 — Cold open (10 min)

Full-screen: `aurad`, the daemon, never examined before. Thousands of
instructions.

**Question:** you have *five minutes* to find where it validates an incoming
command. Not to solve it — to find *where to look*. Write your plan of attack.

Written prediction. This is the real exam of the course: not "read this," but
"where do you even start?" Some will say strings, some xrefs, some strace the
socket. All valid. The point is that they have a *method* now.

Resolved throughout — the whole session is the answer.

---

## 0:25 — Teach A: the method (35 min)

### A1 — Triage: where to spend attention (12 min)

The thesis of the session, stated flat:

> "A real binary has more code than you will ever read. In this job you read maybe
> 2% of it. The entire skill — the thing that separates a reverse engineer from
> someone who merely knows assembly — is choosing *which* 2%. Nobody, and nothing,
> can choose it for you, because it depends on your *goal*. The AI doesn't know
> your goal. You do."

The triage checklist, onto card #5, demonstrated live on `aurad`:

```
 1. What is it?        file, readelf — arch, linkage, stripped?
 2. What does it touch? strace/ltrace — files, network, env
 3. What can it say?   strings — errors, formats, banners, paths
 4. What does it call?  PLT list — crypto? network? crypto+network?
 5. Where's my target?  xref a relevant string / import → the logic
 6. THEN read code.     and only the code triage pointed you to
```

> "Five steps before you read a single instruction. Amateurs open the
> disassembler at address zero and start scrolling. Professionals spend five
> minutes on steps 1–5 and then open the disassembler at the *one function that
> matters.* Watch."

Do it live: string `"bad command"` → xref → the dispatcher → the validator. Under
sixty seconds to the target function in a binary you've "never seen."

### A2 — The hypothesis loop (11 min)

Draw it on the board; it's the spine of everything they've done:

```
        ┌──────────▶ FORM a hypothesis ──────────┐
        │           "this loop is a checksum"     │
        │                                          ▼
   RECORD it                                  PREDICT what you'd
   (notes: confirmed /                        observe if true
    killed / open)                            "sum of input bytes"
        ▲                                          │
        │                                          ▼
        └────────────── TEST it ◀─────────────────┘
              (gdb: feed known input, read the value)
```

> "This is the loop. It's the scientific method with a debugger. Every session
> you've done pieces of it; today you do all of it, out loud, on purpose. And the
> **record** step is the one everyone skips and shouldn't — your notes are how you
> don't re-derive the same thing next week, and how someone else can reproduce
> your work. A finding you can't reproduce isn't a finding."

Note-taking as a professional artifact: the personal RE notebook (in RESOURCES).
Hypotheses dated, evidence linked, dead ends *kept* (a dead end is a result — it
tells the next person not to go there).

### A3 — Recognising shapes (12 min)

Pattern-matching *your own*, so you can spot when the AI's is wrong. From card #5:

**Crypto and encoding — recognisable by constants:**

| Shape | Tell |
|---|---|
| AES | S-box `0x63 0x7c 0x77 0x7b...`; round structure |
| SHA-256 | init constants `0x6a09e667...`; 64-round loop |
| MD5 | `0x67452301`; magic additive constants |
| base64 | the alphabet string `ABC...789+/`; `>>6`, `&0x3f`, groups of 3/4 |
| CRC32 | a 256-entry table; xor-and-shift per byte |

> "You don't memorise AES. You recognise 'a 256-byte table starting `63 7c 77` —
> that's the AES S-box' and then you *look it up*. That's the S3-tier skill: know
> the smell, then go read. The `shapes_zoo` binary in your pack is fifteen of
> these — learn to sniff them."

**Structural shapes:** state machine (a `switch` on a `state` variable in a loop —
S3), parser (character-class checks, `isdigit`-shaped comparisons, a cursor
pointer advancing), protocol handler (read length, then read that many bytes —
AURA-7's `aurad`).

### A4 — The specialised zoo: recognise, don't memorise (~included in A3's tail / brief)

Explicitly framed as Step-3 territory. ~5 min, pointers only:

| You'll meet | It looks like | You do |
|---|---|---|
| **Packer** (UPX etc.) | tiny `.text`, huge high-entropy `.data`, one weird entry stub | recognise → unpack (often `upx -d`) → analyse the real thing |
| **Anti-debug** | `ptrace(PTRACE_TRACEME)`, timing checks, scanning own bytes for `0xCC` (S7!) | recognise → patch the check or attach differently → read up |
| **Custom VM** | a fetch-decode-execute loop over a "bytecode" array | recognise → recover the VM's opcode table → then it's just RE again |
| **Obfuscation** | opaque predicates, bogus control flow, string encryption (S1's XOR!) | recognise → often deobfuscate dynamically → read up |

Demo two quickly: run `packed_demo` through `strings` (garbage) then note the UPX
signature; show `antidebug_demo` detecting gdb and the one-line patch that
neutralises the `ptrace` check.

> "Nobody has these memorised. You recognise the shape, you name it, you look up
> the specific technique, and then you're back to the fundamentals you already
> have. This is exactly where an AI is genuinely useful — 'I think this is a VM
> dispatch loop, help me recover the opcode semantics.' You supply the
> recognition and the judgment; it supplies the grind. That's the partnership the
> whole course has been building toward."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: the shape zoo + triage (40 min)

Full spec: [`labs/s09-lab.md`](../labs/s09-lab.md).

- **Core** — `shapes_zoo`: identify the algorithm in each of 8 functions by
  constants/structure alone. (base64, CRC32, a Caesar/XOR, a simple state
  machine, etc.) Name it and cite the tell.
- **Stretch** — triage `aurad` cold: produce the 5-step triage note and reach the
  command validator via xrefs. Time yourself.
- **Boss** — `antidebug_demo`: identify the anti-debug technique, neutralise it,
  and get a clean trace. Write the "recognise → look up → apply" chain you
  followed. (Explain-back — this is the S3-skill in action.)

---

## 1:50 — Teach B: the crown jewel — reversing AURA-7 end to end (45 min, extended)

**This is the single most important segment of the course.** The lecturer reverses
AURA-7's licence algorithm *and* wire protocol, live, start to finish, thinking
aloud, **every wrong turn kept in.** Budget 45 minutes — this replaces the normal
Teach B + Lab B split, and it is worth the whole session on its own.

*(This is why S9 has no separate 2:25 Lab B — the demo absorbs it, and students
participate throughout. See the schedule note below.)*

The arc, closing threads opened across five months:

1. **Triage** (5 min) — run the method on `auractl`+`aurad` fresh, out loud.
2. **The licence transform** (12 min) — pick up the S7 watchpoint thread.
   Characterise the shift-xor-accumulate. **Wrong turn:** guess it's CRC32,
   check the constants against card #5 — no table, doesn't match. It's a *custom*
   rolling hash. "Good — I was wrong, and the constants *told* me I was wrong in
   ten seconds. That's why we recognise by evidence, not by vibe." Recover the
   exact recurrence. Write a keygen. Prove it: generate a key, `auractl` accepts.
3. **The config checksum** (8 min) — close the S1/S5 OPEN QUESTION. The
   length-field mismatch from *session one* was a checksum trailer. Compute it,
   forge a fully-valid config. **Walk to the S1 board and cross the open question
   off.** Five months to close that loop — let the room feel it.
4. **The wire protocol** (12 min) — `aurad`'s socket. strace it, then read the
   handler: `[1 byte type][2 byte length][length bytes payload]`. A state machine
   (recognised, A3). Hand-craft a packet with `python`+`socket`, send it, get a
   valid response. AURA-7 is fully understood.
5. **The AI checkpoint** (8 min) — flows straight into the drill below.

Keep a running board of hypotheses: formed, confirmed, killed. By the end the
AURA-7 MAP is complete and the OPEN QUESTIONS board is empty. That visual — five
months of accumulated questions, all closed — is the emotional payoff that
replaces a grade.

---

## 2:15 — Break (10)

---

## 2:25 — Lab B (merged into the demo) / hypothesis-log write-up (30 min)

Because Teach B ran to 45, this block is: students **finish and document**. Each
produces a **hypothesis log** for one AURA-7 component — not just the answer, but
the trail: what they hypothesised, what they predicted, what they observed, what
they killed. This log *is* the deliverable, and it's the thing a grade would
reward if there were grades: the reasoning, not the result.

Seed the drill: **"give a model the full `auractl` licence-check decompilation
and ask it for the exact algorithm. Keep its answer verbatim."**

---

## 2:55 — Falsification Drill + close (5 min)

The highest-stakes drill of the course, because the class built the ground truth
themselves, today, live.

**The claim.** The model's algorithm description — typically fluent and *mostly*
right: *"It computes a CRC32 of the key bytes and compares to a stored value,"* or
a rolling hash with the wrong constant/rotation.

1. *State it.* Written on the board next to the *actual* recurrence the class
   recovered in Teach B.
2. *What would falsify it?* — feed one known key through both the model's claimed
   algorithm and the real binary; compare the intermediate accumulator after two
   bytes.
3. *Observe.* They diverge at byte 2 — the model has the wrong rotation, or
   invented a table that isn't there.
4. *Verdict.* **Wrong in the detail that matters.** Reason: the model produced a
   *plausible member of the "licence hash" family* — right genre, wrong specifics
   — because it pattern-matched to common implementations instead of tracing this
   one. Right shape, wrong function. And here's the point: **you could tell,
   instantly, because you had the real recurrence in your hand.** Someone without
   it would have shipped the model's version and written a keygen that produces
   valid-looking, invalid keys.

> "That is the whole course in one drill. The model got you 90% there in one
> second — genre right, structure right. The last 10% was a rotation constant,
> and it was wrong, and it would have broken everything, and *you caught it in
> ten seconds because you can read the evidence.* You don't reject the model.
> You don't worship it. You use it for the 90% and you *are* the 10%."

**Cold-open reveal:** point at the method they wrote at 0:15 versus what they
actually did. Most of them had the right instinct. That instinct is what five
months built.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 9 | The licence algorithm is CRC32 (or rolling hash w/ wrong constant) | ✗ Wrong (right genre, wrong specifics) | Pattern-matched to the common "licence hash" family; wrong rotation/constant. Diverges from the real recurrence at byte 2. Caught instantly *only* because the class had recovered the true algorithm by hand |

---

## Lecturer notes

**This session justifies the whole course. Protect the 45-minute demo above
everything.** If you must cut, cut Lab A Boss and A4's second live demo — never
the AURA-7 reverse or the closing of the OPEN QUESTIONS board.

**Closing the S1 open question is a real emotional beat — stage it.** Physically
walk to the old board, physically cross it off. Students opened that question in
week one. Landing it in week 17 is the payoff that an ungraded course otherwise
lacks. Don't rush past it.

**The wrong turns are the content here, not decoration.** A student's biggest
misconception is that experts don't get stuck. Forty-five minutes of an expert
getting stuck and recovering, methodically, is the most valuable thing they see
all course. Ham it up. Be visibly wrong. Recover visibly.

**The specialised zoo (A4) tempts overreach.** It is pointers only. Resist
teaching how to write a VM devirtualizer. "Here's what it looks like, here's the
word to search, here's that it's normal to look it up" — that's the entire
learning objective. Depth is S3-tier and out of scope by design.

**Running long (certain).** Merge Lab B into the demo as written; cut Lab A Boss;
compress A4 to pure pointers. The demo and the drill are non-negotiable.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-9)

- **Read:** *Practical Binary Analysis* ch. 5–6; skim a writeup of a real crackme
  or a published malware teardown for the *method*, not the target.
- **Do:** full teardown of a difficulty-3/4 crackme, keeping a proper hypothesis
  log. The log matters more than the solve.
- **Crackme:** crackmes.one difficulty 4, or a first pwn.college module.
- **Self-check:** 5 questions, answers included.
