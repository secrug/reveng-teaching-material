# Lab 6 — Build a map

**Time:** Lab A 40 min + Lab B 30 min · **Pack:** fresh `auractl` for Ghidra,
`s06/overlap`

---

## Lab A — Annotate in Ghidra

### Core — Name six functions

Import `auractl`, auto-analyse, and name + comment 6 functions into a clean map.
**Navigate by cross-reference, not by scrolling** — start from a string
(`"invalid licence"`, `"activate"`) or a PLT call and xref your way to code.

**Deliverable:** a Ghidra project (or screenshots) with 6 renamed, commented
functions, and one sentence per function on how xrefs led you there.

### Stretch — Retype and watch it improve

Retype the arguments of 3 functions using your S4/S5 recoveries (`undefined8` →
`char *`, etc.). Note where the decompiler output got more readable as a result.

**Deliverable:** before/after decompiler snippets for one function, showing the
improvement from retyping.

### Boss — Catch the decompiler (explain-back)

Find **one function where the decompiler is provably wrong** and prove it against
the disassembly.

**Deliverable:** what the decompiler claimed, what the bytes actually do, and the
evidence (a gdb value or a disassembly line). Explain to a neighbour, notes closed.

#### Solution outline

BUILD-PLAN §S6 guarantees ≥2 decompiler errors in `auractl`: (a) a signedness
misread that changes a comparison's meaning, and (b) the `check_license` decoy
whose return value is unused. Either qualifies. The proof must be against
*evidence*, not a second opinion — "gdb shows the value behaves as the bytes say,
not as the decompiler wrote."

---

## Lab B — Three-way comparison

Pick one `auractl` function. Produce a four-column document:

| Disassembly (facts) | Decompiler output | LLM output | Verdict + evidence |
|---|---|---|---|

At least one row must be a **discrepancy resolved by observation** (a gdb value,
an offset, an xref result). This is the Falsification Drill extended to a full
block — everyone leaves with a written "where each generator was right, where it
was wrong, how I knew."

#### Solution outline

The natural discrepancy is `check_license`: decompiler shows `return 1`, LLM
narrates it as the licence check, disassembly + xref show its result is discarded.
Verdict: decoy, both generators misled, resolved by xref. Any function works, but
this one makes the point hardest.

---

## TA notes

The lesson isn't "Ghidra is bad" — 95% of its output is correct and fast. The
lesson is calibration: it's a generator, you verify generators, and you *can*
because of S1–S5. Push back on any student who swings to "so the decompiler is
useless" as hard as on one who trusts it blindly. Both missed the point.
