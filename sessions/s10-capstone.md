# Session 10 — Capstone: humans, machines, and a target nobody has seen

**The one idea:** prove the thesis on themselves. Not "the lecturer says AI has
limits" — "we raced it, and we watched exactly where it broke, and now we own
that knowledge as evidence."

---

## Outcomes

1. Describe where RE is used professionally and the legal/ethical boundaries.
2. State, from a full course of evidence, what AI does well and badly on binaries.
3. Reverse an unfamiliar binary under time pressure using the full method.
4. Articulate — from lived experience in the race — why fundamentals are the
   thing that lets you *direct* AI rather than be misled by it.
5. Know where to go next.

---

## Prep checklist

- [ ] `s10/` pack: `enigma` — a **fresh AURA-7 variant** nobody has seen, with a
      different licence recurrence and a planted decoy. Three difficulty-matched
      copies if you want to hand different tables slightly different targets.
- [ ] The complete **AI Scoreboard** from S1–S9, printed large. This is the
      centrepiece — nine sessions of evidence.
- [ ] All five reference cards; the RESOURCES map printed.
- [ ] Table signage: **A — NO AI**, **B — AI ONLY**, **C — HUMAN + AI**.
- [ ] A prize. Genuinely — an ungraded course needs the race to have stakes.
      Chocolate works. (See notes: the *winner* is not the point.)
- [ ] Cast: `s10-demo.cast` (a reference solve of `enigma`, for after).

---

## 0:00 — Warm-up (15 min): the scoreboard as evidence

No new questions. Put the full S1–S9 scoreboard on screen and read it as a body of
evidence, letting the room reconstruct each failure:

| S | What AI got wrong | The underlying reason |
|---|---|---|
| 1 | invented behaviour from strings | pattern-matched a format string to a story |
| 2 | register value after 32-bit write | missed an arbitrary ISA rule |
| 3 | loop bound off by one | produced the *common* loop, not this one |
| 4 | missed a function argument | stopped at the first recognisable call |
| 5 | struct padding offset | summed field sizes; padding invisible in source |
| 6 | narrated a decoy function | can't model *intent*, only bytes |
| 7 | subtly broken gdb script | 90% right tooling, wrong detail |
| 8 | hook a `strcmp` that isn't called | textbook answer, not this binary |
| 9 | wrong licence algorithm specifics | right genre, wrong constant |

Ask the room: **what's the pattern across all nine?** Guide them to it:

> "Every single failure is the same failure wearing different clothes. The model
> produces the *statistically likely* answer, and it breaks precisely where this
> binary *departs* from the likely — the arbitrary rule, the padding, the decoy,
> the custom constant. And in every case, you caught it with *evidence* — a
> register, an offset, a breakpoint. That's not nine anecdotes. That's a law. And
> you derived it yourselves."

---

## 0:15 — Teach A: where RE lives, and the law (30 min)

Slightly longer, no cold open today — the race is the cold open.

### A1 — The field (12 min)

Where these skills go, honestly:

- **Vulnerability research** — finding bugs in software you don't have source to.
  (The S4 return-address moment was a keyhole into this.)
- **Malware analysis** — understanding what hostile code does. (We did none live,
  on purpose; here's what the job actually involves and how containment works.)
- **Firmware / IoT / embedded** — AURA-7's whole premise. Often no symbols, weird
  architectures (your S8 ARM64 minute matters here), physical devices.
- **Interoperability & preservation** — talking to undocumented formats and
  protocols; keeping old software alive. (Frequently the *legal* face of RE.)
- **Anti-cheat, DRM, licensing** — the AURA-7 licence thread, as an industry.
- **Compliance / security audit** — verifying what a vendor's binary really does.

### A2 — The law and the ethics (12 min)

Do this properly; it's a duty of the course.

> "Everything you did this semester, you did to binaries *I* gave you, that *I*
> made, for *learning*. That is the safe square. Outside it, the ground is real
> and jurisdiction-dependent."

- **It varies by country.** The EU permits reverse engineering for
  interoperability under specific conditions; the US DMCA restricts circumventing
  access controls with research/interop exceptions that shift periodically;
  contract law (the EULA you clicked) can forbid what statute would permit. *This
  is not legal advice; it's a map of where the landmines are — check your
  jurisdiction and the licence.*
- **Responsible disclosure.** If you find a vulnerability, there is a right way:
  tell the vendor, give them time, coordinate. Not a bug-bounty lecture — a
  professional-norms one.
- **The bright line.** A lab binary is not someone's production server. Skill does
  not confer permission. The most capable people in this room have the most
  responsibility to stay on the right side of that line.

### A3 — The honest AI ledger (6 min)

Both columns, from the evidence, fairly:

| AI genuinely excels at | AI reliably fails at |
|---|---|
| bulk renaming / first-pass annotation | exact offsets, padding, alignment |
| recognising *known* algorithms fast | this binary's specific constants |
| writing tooling scaffolds (then you fix) | arbitrary ISA/ABI rules |
| summarising large code you'd skim anyway | modelling intent (decoys, traps) |
| suggesting hypotheses to test | deciding *what's worth looking at* |
| explaining a technique you looked up | admitting it doesn't know |

> "This is not a course that hates AI. Look at the left column — it's genuinely
> powerful, and you should use all of it. The course's claim is narrow and
> proven: the left column is *acceleration*, the right column is *the job*, and
> you can only tell which is which — you can only catch the right-column failures
> and exploit the left-column wins — if you have the fundamentals. The person who
> can't read a stack frame can't use either column safely. You can. That's what
> changed this semester."

---

## 0:45 — Break (10)

---

## 0:55 — The Race (75 min)

The capstone. `enigma` — a fresh AURA-7 variant, unseen. Split the room into
three kinds of table:

- **Table A — NO AI.** Tools, brains, notes. No model, at all.
- **Table B — AI ONLY.** They may relay the model's instructions and type what it
  says, but **may not reason independently or override it.** They are the model's
  hands. (This is the crucial, artificial condition — enforce it.)
- **Table C — HUMAN + AI.** Use everything, however they like. The realistic mode.

**The task** (on screen): recover `enigma`'s licence algorithm and produce one
valid key. First to a *verified* valid key wins; partial credit for a documented
hypothesis log if nobody finishes.

**Run it for 60 minutes.** Circulate. Take notes on *how each table behaves* —
that's the debrief material:

- Table A: slow start, but every step is understood; no dead ends from
  misplaced trust.
- Table B: fast start, then — reliably — a wall. The model mis-identifies the
  algorithm (the S9 failure), or narrates the planted decoy (the S6 failure), and
  the table, forbidden from reasoning, *cannot get off it.* They re-prompt. They
  get variations of the same wrong answer. Watch this happen; it's the whole
  lesson, live.
- Table C: fast start *and* recovery — they use the model for the grind and their
  own judgment at the wall.

**15 minutes: verify and stop.** Establish who has a genuinely valid key (test it
against `enigma` on screen — evidence, to the end).

---

## 2:10 — Break (5, short — save time for the debrief)

---

## 2:15 — Debrief: how each table *failed* (35 min)

This is where the course lands. Not "who won" — **how each table failed**, because
the failures are the evidence.

Structured questions to each table, in order:

**Table B first (the point).**
- Where did you get stuck? *(the decoy, or the wrong algorithm)*
- What did you do when the model was wrong? *(re-prompted — and got the same
  genre of wrong answer)*
- Could you tell it was wrong? *(usually: no, or only suspected)*

> "Table B had the fastest first ten minutes in the room and then hit a wall they
> could not climb, because climbing it required exactly the thing they'd given
> up: independent reasoning from evidence. This isn't a knock on the model — it's
> a demonstration that the model plus someone who can't check it is a confident
> machine for producing wrong answers. That was you, deliberately, for an hour.
> Remember the feeling."

**Table A.**
- How far did you get? Was every step solid?
- What did you wish you'd had? *(the model's speed on the boring parts)*

**Table C.**
- Where did the model help most? *(the grind — renaming, first-pass, the known
  parts)*
- Where did you have to overrule it? *(the wall — same wall as Table B)*
- **The key question:** how did you *know* to overrule it?

> "Table C is the real world, and notice the answer to that last question: you
> knew to overrule it because you could read the evidence yourselves. Table C
> isn't 'AI plus vibes.' It's 'AI plus someone who can catch it.' The catching is
> the whole degree. That's the job now. Not doing the RE by hand — *directing the
> machine and knowing when it's lying.* And you can only direct what you
> understand."

Tie it to the S1 opening line, brought back full circle onto the last slide:

> "Session one: *AI moved the bottleneck from 'can you read assembly' to 'do you
> know what to ask, and can you tell when the answer is wrong.'* Table B couldn't
> tell. Table C could. The difference is everything you learned since week one."

---

## 2:50 — Close: where to go next (10 min)

- **The resource map** ([RESOURCES.md](../RESOURCES.md)) — the ladder onward:
  crackmes.one difficulty 4+, pwn.college, CTFs (pwn/rev categories),
  microcorruption, open-source Ghidra plugins to read.
- **Fields to specialise into**, mapped to A1.
- **The one habit to keep:** the hypothesis log. "If you keep one thing from this
  course, keep the notebook. Form, predict, test, record. It's the method under
  everything, and it's yours now."
- Prize to the winning table; but the last word is the debrief, not the prize.

Final slide — the course thesis, unchanged from Session 1, now earned:

> AI moved the bottleneck from *"can you read assembly"* to *"do you know what to
> ask, and can you tell when the answer is wrong."* **Both are fundamentals — and
> now you have them.**

---

## Scoreboard entry — the meta-entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 10 | (Table B's model) `enigma`'s algorithm is [wrong] | ✗ Wrong | Same failure as S9, discovered by students racing it: right genre, wrong specifics / narrated the decoy. Table B couldn't recover; Table C could — because Table C could read the evidence |

---

## Lecturer notes

**The race must be genuinely enforced, especially Table B.** If Table B students
quietly reason on their own, the lesson evaporates. Frame it as a game with a
rule, seat a TA there if you can, and make clear the *point* of the constraint
(you're the model's hands — that's the experiment). Rotate which students are
Table B across a repeat offering; it's the least fun table and the most
instructive.

**`enigma` must actually defeat the AI-only path.** It carries the same species of
traps proven across S6/S9 (a decoy + a custom constant). Verify against a current
model *before the session* that AI-only genuinely stalls — see `BUILD-PLAN.md`
§S10. If models have improved and it doesn't stall, that's not a failure of the
course — it's the most interesting possible debrief, and you should run it as one:
"the wall moved; here's where it is now; the *method* for finding the wall didn't
change." Do not fake a stall; the course's credibility is honesty about the tools.

**Don't let "who won" swamp "how each failed."** The prize is bait to make the
race real. The debrief is the session. Guard the 35 minutes for it — if the race
overruns, cut it at 55 and protect the debrief, not the other way around.

**End on earned confidence, not fear.** The failure mode of this session is
sending students out thinking "AI is bad." The correct exit state is "AI is
powerful and I am the one who can wield it, because I can check it." Land the
final slide warmly. They earned it.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-10)

- **Do:** enter one CTF (rev or pwn category). Any. The point is the arena.
- **Read:** pick your field from A1 and read one real writeup in it.
- **Keep:** the hypothesis-log habit, forever.
