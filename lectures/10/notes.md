# Lecture 10 — Capstone: humans, machines, and a target nobody has seen

---

## 1. The scoreboard, as evidence

Over nine lectures the class has kept a running record: every time a model made a
claim about a binary, what the claim was, whether it held up, and — the useful column
— *why it failed*. Read as a body, it is not a collection of anecdotes about a tool
being imperfect. It is a dataset, and it has a pattern.

| Lecture | What the model got wrong | The underlying reason |
|---|---|---|
| 1 | invented behaviour from strings | pattern-matched a format string into a story |
| 2 | a register value after a 32-bit write | missed an arbitrary ISA rule |
| 3 | a loop bound, off by one | produced the *common* loop, not this one |
| 4 | missed a function argument | stopped at the first recognisable call |
| 5 | a struct field offset | summed sizes; padding is invisible in source |
| 6 | narrated a decoy function | cannot model intent, only bytes |
| 7 | a subtly broken gdb script | tooling 90% right, one detail wrong |
| 8 | hook a `strcmp` that isn't called | textbook answer, not this binary |
| 9 | the wrong licence constant | right genre, wrong specifics |

Look down the last column and the same failure appears nine times in different
clothing. In every case the model produced the **statistically likely** answer, and
in every case it broke precisely where the binary **departed from the likely** — the
arbitrary rule, the padding, the decoy, the custom constant, the exact offset. And in
every case it was caught with **evidence** — a register, a memory dump, a breakpoint,
a byte at an offset — that a student could read because they had built the skill by
hand.

That is not nine coincidences. It is one law, observed nine times. And you derived it
yourselves, which is the only way it was ever going to be convincing.

---

## 2. Where these skills go

Reverse engineering is not a self-contained puzzle hobby; it is a working skill with
several professional homes.

**Vulnerability research** — finding bugs in software you do not have the source to.
The return-address moment in Lecture 4 was a keyhole into this. It is how security
researchers find flaws before attackers do, and how attackers find them first.

**Malware analysis** — understanding what hostile code does. We deliberately used no
live samples; in practice this is done in isolated, monitored environments, and the
containment is a discipline of its own. The reading skills are exactly the ones you
have.

**Firmware and embedded / IoT** — AURA-7's whole premise. Often no symbols, unusual
architectures (your ten minutes of ARM64 in Lecture 8 matter here), and physical
devices whose behaviour you can only understand by taking the firmware apart.

**Interoperability and preservation** — talking to undocumented file formats and
network protocols, and keeping old software alive after its vendor is gone. This is
frequently the most clearly *lawful* face of reverse engineering, and historically
its most legally protected.

**Anti-cheat, DRM, licensing** — the AURA-7 licence thread, as an entire industry, on
both sides.

**Compliance and audit** — verifying that a vendor's binary actually does what the
vendor claims, when you cannot see its source.

---

## 3. The law, and the ethics

Everything you did this semester, you did to binaries this course provided, that this
course made, for the purpose of learning. That is the safe square. Outside it, the
ground is real and depends on where you are.

**It varies by jurisdiction, and this is not legal advice — it is a map of where the
landmines are.** In the EU, reverse engineering for interoperability is permitted
under specific conditions. In the US, the DMCA restricts circumventing access
controls, with research and interoperability exceptions that shift over time. And
contract law is separate from both: the licence agreement you clicked can forbid what
statute would otherwise allow. Before you take anything apart that is not yours to
take apart, check your jurisdiction and the licence.

**Responsible disclosure.** If you find a vulnerability in real software, there is a
right way to handle it: tell the vendor, give them reasonable time to fix it,
coordinate the timing of any public description. This is a professional norm, not a
legal technicality, and the community takes it seriously.

**The bright line.** A lab binary is not someone's production server. Skill does not
confer permission. The most capable people in this room carry the most responsibility
to stay on the right side of that line, precisely because they are the ones able to
cross it.

---

## 4. The honest ledger

It would be a misreading of this whole course to leave believing that AI is
untrustworthy and should be avoided. That is as wrong as the belief the course set out
to correct. Both columns are real.

| The tool genuinely excels at | The tool reliably fails at |
|---|---|
| bulk renaming, first-pass annotation | exact offsets, padding, alignment |
| recognising *known* algorithms fast | this binary's specific constants |
| writing tooling scaffolds (you then fix) | arbitrary ISA and ABI rules |
| summarising large code you would skim | modelling intent — decoys, traps |
| suggesting hypotheses to test | deciding what is worth looking at |
| explaining a technique you looked up | admitting when it does not know |

Look at the left column honestly. It is a large multiplier on your effectiveness, and
using all of it is correct, not lazy. The course's claim was never that the tool is
useless. It is that the left column is *acceleration* and the right column is *the
job*, and you can only tell which is which — you can only harvest the left and catch
the right — if you have the fundamentals. The person who cannot read a stack frame
cannot safely use either column. You can. That is what changed this semester.

---

## 5. The race

The rest of this session is an experiment, run on yourselves. A binary nobody has
seen — a variant of AURA-7 with a different algorithm and a fresh decoy — and three
kinds of team.

- **Table A — no AI.** Tools, notes, and your own reading.
- **Table B — AI only.** You may relay the model's instructions and type what it says.
  You may not reason independently or override it. You are the model's hands.
- **Table C — human and AI.** Anything goes. The realistic mode.

The task: recover the licence algorithm and produce one valid key. First verified key
wins; a documented hypothesis log wins if nobody finishes.

Table B's constraint is artificial on purpose. It isolates a single question: what
does pure delegation to the tool, with no independent judgement behind it, actually
get you? You will not have to take the answer on faith. You will watch it happen at
your own table.

The prediction, stated plainly before you start: Table B will have the fastest first
ten minutes in the room, and will then hit a wall it cannot climb — because climbing
it requires exactly the thing that table gave up. Remember how that feels.

---

## 6. What the race is really measuring

When the debrief comes, the question is not who won. It is **how each table failed**,
because the failures are the evidence.

Table B, most likely, got moving fastest and then stalled — the model mis-identified
the algorithm, or confidently narrated the planted decoy, and the table, forbidden
from reasoning past it, re-prompted and got variations of the same wrong answer. They
could not tell it was wrong, because telling would have required reading the evidence
themselves.

Table A was slow to start and solid all the way — every step understood, no time lost
to misplaced trust, and also no acceleration on the boring parts.

Table C, the realistic mode, was fast *and* recovered at the wall — the same wall
Table B hit — because when the model failed, they could read the evidence themselves
and knew to overrule it. And that last phrase is the whole point: Table C is not "AI
plus vibes". It is "AI plus someone who can catch it". The catching is the entire
skill, and it is the only thing that separates Table C from Table B.

---

## 7. The thesis, earned

Lecture 1 opened with a claim, and you were asked to take it on trust:

> AI moved the bottleneck from *"can you read assembly"* to *"do you know what to ask,
> and can you tell when the answer is wrong."* Both are fundamentals.

You now have the evidence for it, and you generated all of it. Table B could not tell
when the answer was wrong. Table C could. The scoreboard is nine documented instances
of *not being able to tell* being the thing that mattered. The difference between the
two tables is everything this course taught since week one.

The tools will keep improving. The wall will move — the class of binary that defeats
pure delegation will get narrower and stranger. But the *method* for finding the wall
does not change, and the ability to read the evidence when you reach it does not go
out of date. When the tool is right, that ability lets you move fast. When it is
wrong, that ability is the only thing standing between you and a confident, plausible,
wrong answer.

That is the job now. Not doing the reverse engineering by hand — directing the machine
that does most of it, and knowing, from evidence, when it is lying. And you can only
direct what you understand.

---

## 8. Where to go next

- **crackmes.one** past difficulty 3, and **pwn.college** if the security side pulled
  at you.
- **CTF competitions**, reverse-engineering and pwn categories — the fastest way to get
  good is a team that does this every week.
- **The fields in §2**, if one of them is where you want to end up. Read one real
  write-up in it.
- **The one habit worth keeping forever:** the hypothesis log. Form, predict, test,
  record. It is the method underneath everything, and it is yours now.

---

## Summary

- The scoreboard is one failure observed nine times: the tool gives the statistically
  likely answer and breaks where the binary departs from likely. You derived this
  yourselves.
- Reverse engineering has real professional homes: vulnerability research, malware
  analysis, firmware, interoperability, DRM, audit.
- The law varies by jurisdiction and by licence; disclosure is a professional norm; a
  lab binary is not someone's server. Skill is not permission.
- Both columns of the ledger are real. The left is acceleration, the right is the job,
  and only fundamentals let you tell them apart.
- The race measures how each team *fails*. AI-only stalls at the wall; human+AI
  recovers, because it can read the evidence.
- The thesis, now with evidence: the bottleneck is knowing what to ask and telling
  when the answer is wrong. Both are fundamentals, and now you have them.

## Reading

- Enter one CTF, any, in a reverse or pwn category. The point is the arena.
- Read one real write-up in whichever field from §2 you are drawn to.
- Keep the notebook.
