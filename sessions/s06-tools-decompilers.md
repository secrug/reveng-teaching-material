# Session 6 — Tools: disassembly, decompilation, disciplined static analysis

**The one idea:** the decompiler is a hypothesis generator of exactly the same
species as the LLM. It is enormously useful and it is sometimes wrong, and you
can now tell which — because for five sessions you did its job by hand. This is
the session where the entire course argument clicks.

---

## Outcomes

1. Explain linear-sweep vs recursive-descent disassembly and why perfect
   disassembly is undecidable.
2. Describe what a decompiler does (lift → IR → dataflow → structuring) and name
   its standard failure modes.
3. Navigate a binary in Ghidra by cross-references, not by scrolling.
4. Rename and retype functions/variables as *recording hypotheses*, and watch the
   decompiler output improve as a result.
5. Find two places the decompiler is wrong on a real function and prove each
   against the disassembly.
6. Place decompiler output, LLM output, and ground truth on the same axis:
   generators vs evidence.

---

## Prep checklist

- [ ] Ghidra installed and **launch-tested on the image** (JDK, project dir
      writable) — the #1 failure point of this session
- [ ] `s06/` pack: `overlap` (code/data ambiguity demo), and a fresh copy of
      `auractl` for a clean Ghidra project
- [ ] Reference card **#4 (gdb)** printed — issue today, needed heavily from S7
- [ ] Projector resolution checked — Ghidra's UI is dense; bump font in
      Edit▸Tool Options
- [ ] Casts: `s06-demo1.cast` (Ghidra tour), `s06-demo2.cast` (decompiler lies)

---

## 0:00 — Warm-up (15 min)

1. `[rdi + rcx*4]` vs `[rdi + 0x10]` — which is an array, which a field, why?
2. A struct has `char` at +4 and `int` at +8. What's between them and why?
3. `sizeof(struct{int;char;int;})` — number, with reasoning.
4. Where does a `malloc`'d object's pointer come back?
5. From the AURA-7 map: what's still open? *(the checksum)*

---

## 0:15 — Cold open (10 min) — and the reveal students have waited for

Slide: the same `auractl` function shown three ways, side by side:

- **Left:** the raw disassembly (what they've read for five sessions).
- **Centre:** *blank — "the decompiler, revealed in 15 minutes."*
- **Right:** *blank — "an LLM, revealed in 15 minutes."*

Say it:

> "Five sessions ago I told you that you'd get the decompiler today, and that
> your first job with it would be to catch it lying. Today's the day. But first —
> why did I make you wait?"

**The question:** *A tool that turns this* (point left) *into readable C in one
click has existed for twenty years. Why did I refuse to let you use it?*

Written prediction, two minutes. This is the meta-cold-open of the whole course.
Collect a few aloud. Then Teach A answers it by showing what the tool actually is.

---

## 0:25 — Teach A: what these tools actually are (35 min)

### A1 — Disassembly is not trivial (10 min)

The naive belief: "bytes → instructions is just a lookup." Kill it.

- **Linear sweep** — decode start to end, one instruction after another. Fast.
  Wrong the instant data sits inside `.text` (a jump table, an inlined constant):
  it decodes the data as instructions and desynchronises.
- **Recursive descent** — follow control flow from entry points. More accurate,
  but indirect jumps (`jmp rax`, S3!) mean it *cannot know every target*.

Live on `overlap`: a jump table embedded in `.text`. Show objdump misreading the
table bytes as bogus instructions right after the indirect jump.

> "Telling code from data in a stripped binary is **undecidable** in general —
> provably, not just hard. Every disassembler you'll ever use is making educated
> guesses. Ghidra guesses very well. It still guesses. That's failure mode zero,
> and it's underneath everything else today."

### A2 — What a decompiler does (13 min)

The pipeline, on the board — deliberately parallel to the S1 compilation pipeline,
drawn as its mirror image:

```
 machine code ─▶ disassemble ─▶ lift to IR ─▶ dataflow analysis ─▶ structure ─▶ C-like output
                    (guess       (normalise    (types, variable    (loops,
                     code/data)   the ISA)      recovery)           if/else)
```

Every stage is inference, and each has a signature failure:

| Stage | What it guesses | Failure mode you'll see |
|---|---|---|
| disassemble | code vs data | garbage functions, misaligned instrs |
| lift | instruction meaning | usually solid; rare on exotic instrs |
| dataflow | variables & types | invented locals, `undefined4`, wrong signedness |
| structure | loops/branches | `goto` soup, mis-nested loops, wrong bounds |

> "Look at that diagram. It is the S1 pipeline run *backwards*, and every
> backwards arrow is a guess — because, S1, the information was destroyed. The
> decompiler cannot un-destroy it. It produces the *most likely* source. Most
> likely is not actual. Where have you heard that before?"

Name the standard lies explicitly, onto their notes:
1. Wrong types (`int` for a pointer, unsigned for signed).
2. Invented variables that don't correspond to anything.
3. Dropped side effects (a flag set, a global touched).
4. Mis-structured / mis-bounded loops (S3's off-by-one, now automated).
5. Wrong calling convention → wrong or missing arguments (S4).
6. Missed indirect calls → whole call graph edges absent.

Note: this is not "decompilers are bad." They are one of the best tools in the
field. It is "they are *generators*, and you verify generators."

### A3 — The Ghidra tour (12 min)

Live. Import `auractl`, auto-analyse, then teach navigation by **cross-reference**,
because scrolling is how amateurs use Ghidra:

- Symbol Tree / Functions list.
- **Xrefs** — right-click a function/string/global → References. "Who calls this?
  Who touches this global?" This is the core navigation primitive of all static
  analysis. The string `"invalid licence"` → xref → the code that prints it →
  xref its caller → the check. **Working backwards from a string to the logic is
  how real triage starts.** (Preview of S9.)
- The function graph (the CFG from S3, drawn for you).
- The decompiler window beside the disassembly.

Then the money move: `undefined4 param_1` in the output. Retype it to `char *`
using what they recovered in S5 — and the decompiler *rewrites the function* more
readably in real time.

> "Renaming and retyping isn't decoration. Every rename is you *recording a
> hypothesis*, and the tool propagates it. You are teaching the decompiler what
> you deduced by hand. The human supplies the ground truth; the tool does the
> bookkeeping. That's the correct relationship — and it's the same relationship
> you want with the LLM."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: build a map (40 min)

Full spec: [`labs/s06-lab.md`](../labs/s06-lab.md).

- **Core** — in Ghidra, name and comment 6 functions of `auractl` into a clean
  map. Use xrefs to find them, not scrolling.
- **Stretch** — retype the arguments of 3 functions using S4/S5 recoveries; note
  where the decompiler output improved.
- **Boss** — find **one function where the decompiler is provably wrong**, and
  prove it against the disassembly. Document: what it claimed, what the bytes say,
  how you know. (Explain-back — and this becomes the drill.)

The Boss tier is not optional in spirit even if students skip it: you'll surface
a decompiler error for the whole room at 2:55 regardless. The lab just lets the
fast ones find their own.

---

## 1:50 — Teach B: live demo — catching the decompiler (25 min)

The centrepiece. Take a function in `auractl` where the decompiler is wrong — the
build plan guarantees at least two such spots (see `binaries/BUILD-PLAN.md` §S6).

**Error 1 — a dropped/misread operation.** The decompiler shows clean C; the
disassembly has an operation the output doesn't reflect (e.g. a signedness the
decompiler got backwards, changing a comparison's meaning). Show them side by
side. Prove it in gdb with a value that behaves as the *bytes* say and not as the
*decompiler* says.

**Error 2 — the AI-hostile function** (`check_license`): named invitingly, does
almost nothing; the real check is inlined into the caller. The decompiler
faithfully shows `check_license` returning a constant. An LLM asked "how does
licensing work?" will confidently narrate `check_license`. Both are looking at
the decoy.

**Scripted wrong turn:** *you* start by reading `check_license` too. "OK, so the
licence check just returns 1, that seems too easy—" stop. "Wait, who even calls
this? Let me xref it." It's called once and the result ignored. The real logic is
elsewhere. Recover with the xref.

> "The decompiler didn't lie about `check_license` — it's genuinely a function
> that returns 1. It lied by *omission of context*: it can't tell you that this
> function is a decoy, because 'decoy' isn't a property of the bytes, it's a
> property of the whole program's intent. Neither the decompiler nor a model
> reasons about intent. You do."

**Now populate the cold open's three columns:**

| Disassembly (evidence) | Decompiler (generator) | LLM (generator) |
|---|---|---|
| the bytes; ground truth | plausible C; wrong on error 1, distracted by decoy | fluent prose; confidently narrates the decoy |

> "Two generators, one source of truth. The decompiler and the model are the same
> kind of thing — they produce likely output. The disassembly, plus the running
> program, is the only evidence. Your whole job is to run the generators to save
> time, and then *check them against evidence* — which you can only do because
> you spent five sessions learning to read the evidence. That's why you waited."

**The honest counterweight — say it, don't skip it:**

> "And yet: the decompiler just turned 200 lines of assembly into readable C in
> one second, correctly, for 95% of these functions. The model renamed forty
> variables faster than any of you could. These tools are *phenomenal*. The point
> was never that they're useless. The point is that the last 5% is where the
> answer usually hides, and finding it needs you."

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: three-way comparison (30 min)

Students pick one `auractl` function and produce a three-column document:
disassembly facts | decompiler output | LLM output — and a fourth column,
**verdict + evidence**, reconciling them. At least one row must be a discrepancy
resolved by observation (a gdb value, an offset, an xref).

This *is* the Falsification Drill, extended to a full block because it's the
thematic heart of the course. Everyone leaves with a written artifact of "here's
where each generator was right, here's where it was wrong, here's how I knew."

---

## 2:55 — Falsification Drill + close (5 min)

Consolidate rather than start fresh — students have been doing the drill for 30
minutes.

**The claim** (collected from the room): *"The licence check is in
`check_license`."* — asserted by the LLM, and consistent with the decompiler's
tidy rendering of that function.

1. *State it.*
2. *What would falsify it?* — if it were the real check, its return value would
   *matter*: something would branch on it. So xref it and check whether any
   caller uses the result.
3. *Observe.* One caller; result discarded; the actual branch uses a value
   computed inline. Falsified.
4. *Verdict.* **Wrong — decoy.** Reason: both generators reported a real property
   of the bytes (the function returns a constant) but neither could represent
   *intent* (it's bait). Intent is the human's department. Record it — this is
   the scoreboard's most important entry so far.

**Close — the cold-open answer, stated plainly:**

> "Why did you wait for the decompiler? Because a tool that produces confident
> plausible output is dangerous in the hands of someone who can't check it, and
> safe — powerful — in the hands of someone who can. For five sessions you became
> the person who can check. Now go use the power tools. All of them. Including the
> model. You've earned them, and more importantly, you can catch them."

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 6 | The licence check lives in `check_license` | ✗ Wrong (decoy) | Both decompiler and LLM reported a true fact about the bytes (returns constant) but neither models *intent*; the function is bait, real check is inlined in the caller. Found via xref: return value is unused |

---

## Lecturer notes

**Ghidra will fail to launch on someone's machine.** Guaranteed. Have the
`s06-demo1.cast` running and a shared-box Ghidra ready. Do not spend fifteen
minutes debugging one JDK in front of thirty people — pair that student up and
move on.

**This is the thesis session. Land the parallel or the course loses its spine.**
The single sentence students must leave with: *the decompiler and the LLM are the
same kind of thing — generators — and evidence is a different kind of thing.* If
they get only that, the session succeeded.

**Do not let it become anti-AI.** The honest counterweight in Teach B is
mandatory, not optional. A room that concludes "AI bad, hand-reading good" has
misunderstood as badly as a room that concludes "AI solves everything." The
lesson is calibration, not rejection.

**Running long (you will).** Cut Lab A Boss (the whole-room error at 2:55 covers
it), then A1's `overlap` demo (but *state* that code/data is undecidable — it
matters in S8). Protect the three-way comparison; it's the point.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-6)

- **Read:** *The Ghidra Book*, ch. 1–5 (skim, 30 min).
- **Do:** decompile a program you wrote yourself; find the *first* thing Ghidra
  gets wrong about code you have the source to. (Powerful precisely because you
  know the truth.)
- **Crackme:** crackmes.one difficulty 2–3 — solve once with Ghidra, then verify
  the key claim in gdb.
- **Self-check:** 5 questions, answers included.
