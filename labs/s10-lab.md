# Lab 10 — The Race

**Time:** 75 min race + 35 min debrief · **Pack:** `s10/enigma` (fresh AURA-7
variant), table signage

This is not a tiered lab — it's the capstone experiment. Full framing is in the
[session doc](../sessions/s10-capstone.md). This file is the operational
run-sheet.

---

## Setup (before students arrive)

- Three table zones signed **A — NO AI**, **B — AI ONLY**, **C — HUMAN + AI**.
- Assign students to tables. Roughly equal size; put a TA at Table B to enforce
  the constraint.
- `enigma` staged on every machine. It has a **different licence recurrence** from
  the AURA-7 they know, plus a planted **decoy** function.
- The task on screen: *Recover `enigma`'s licence algorithm and produce one valid
  key. Winner = first verified valid key. No finish? Best hypothesis log wins.*

## The rules (read them aloud)

- **Table A:** no AI of any kind. Tools, notes, brains.
- **Table B:** you are the model's hands. You may paste its output, run its
  commands, type what it says. You may **not** reason past it, override it, or
  solve independently. If it's stuck, you re-prompt — you don't think for it.
- **Table C:** anything goes. Realistic mode.

The Table B constraint is artificial *on purpose* — it isolates "what does pure AI
delegation get you?" Enforce it or the experiment is worthless.

## Running it (60 min)

Circulate and **take notes on behaviour**, per table — this is the debrief
material:

- Timestamp when each table finds the licence function.
- Note the moment Table B hits the wall (mis-identified algorithm, or narrating
  the decoy) and what they do next (re-prompt → same genre of wrong answer).
- Note where Table C overrules the model, and *how they knew to*.

## Verify + stop (15 min)

Test candidate keys against `enigma` live, on screen — evidence to the very end.
Establish who has a genuinely valid key.

## Debrief (35 min) — the actual point

Run the structured questions from the session doc, **Table B first.** The lesson
is *how each table failed*, not who won:

- Table B: fastest start, hit an unclimbable wall, couldn't tell the model was
  wrong.
- Table A: slow, solid, every step understood.
- Table C: fast *and* recovered — because they could read the evidence when the
  model failed.

Land the closing thesis (session doc). Prize to the winner; **last word is the
debrief.**

---

## If AI-only does *not* stall (contingency)

If models have improved enough that Table B finishes: **do not fake a stall.** Run
it honestly as the most interesting possible debrief — "the wall moved; here's
where it is now; the *method* for finding walls didn't change; here's the class of
target that still breaks it." The course's credibility is its honesty about the
tools. See `binaries/BUILD-PLAN.md` §S10 for tuning `enigma`'s difficulty upward
(nested custom VM, layered decoys) if you want to restore the stall legitimately.

---

## Deliverable (from every student, any table)

A one-page reflection: which table were you, where did AI help, where did it
mislead (or where did you wish you'd had it), and — the question that matters —
*how would you know if it were wrong?* Collected, not graded; it's the course's
closing evidence that the thesis landed.
