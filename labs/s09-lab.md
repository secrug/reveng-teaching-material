# Lab 9 — The shape zoo + triage

**Time:** Lab A 40 min (Lab B is merged into the 45-min live demo — see the
session doc) · **Pack:** `s09/shapes_zoo`, `aurad`, `antidebug_demo`; card #5

---

## Lab A

### Core — Name the algorithm

`shapes_zoo` contains 8 functions, each a recognisable algorithm. Identify each by
its **constants or structure** and cite the tell. No need to fully reverse them —
recognise the shape.

**Deliverable:** a table.

| fn | algorithm | the tell |
|---|---|---|
| 1 | base64 encode | the `ABC…789+/` alphabet; `>>6`/`&0x3f`; 3→4 grouping |
| 2 | CRC32 | 256-entry table; per-byte xor-and-shift |
| 3 | XOR cipher | single-byte key xor'd across a buffer |
| … | | |

#### Solution outline

Built (BUILD-PLAN §S9) to include: base64, CRC32, a single-byte XOR, a Caesar
shift, a simple state machine (`switch` on a state var in a loop), an FNV-ish
hash, a `memcpy`-shaped copy, and a length-prefixed parser. Grade the *tell*, not
just the name — "it's got a 256-byte table starting `00 00 00 00 77 07 30 96`,
that's the CRC32 table" is the target skill.

### Stretch — Triage `aurad` cold

Produce a 5-step triage note for `aurad` (file / touches / says / calls / target)
and reach the command validator via xrefs. Time yourself from `file` to the target
function.

**Deliverable:** the triage note + the validator's address + your time-to-target.

### Boss — Beat the anti-debug (explain-back)

`antidebug_demo` detects a debugger and misbehaves. Identify the technique,
neutralise it, and get a clean trace. Write the **recognise → look up → apply**
chain you followed.

**Deliverable:** the technique named, the neutralisation, the trace, and the chain
— to a neighbour, notes closed.

#### Solution outline

The technique is `ptrace(PTRACE_TRACEME)` self-attach (a second `ptrace` fails if
already traced) — or a `/proc/self/status` `TracerPid` check. Neutralise by
patching the `ptrace` call to a no-op / return 0, or `LD_PRELOAD` a fake `ptrace`
(S8 skill reused!), or setting the return in gdb. The **chain** is the real
deliverable: this is the S3-tier "recognise the smell, look it up, apply it"
skill made concrete. A student who *knew* the technique from memory is fine; one
who recognised it, searched "linux anti debugging ptrace", and applied what they
found has done exactly what the course wants.

---

## Lab B — merged into Teach B

Because the AURA-7 end-to-end reverse runs 45 minutes with student participation,
the "Lab B" block is a **hypothesis-log write-up**: each student documents one
AURA-7 component as a proper log — hypotheses formed, predictions, observations,
what was killed. The log is the deliverable. Template in
[RESOURCES.md](../RESOURCES.md#the-re-notebook).

---

## TA notes

The anti-debug Boss is where "look it up" gets legitimised out loud. Make sure
students see that *recognising* + *searching* + *applying* is the professional
move for specialised techniques — not memorising every trick. That's the entire
handling of "step 3" material, enacted.
