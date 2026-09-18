# Lecture 6 — Tools: disassembly, decompilation, disciplined static analysis

---

## 1. Why you waited

For five lectures you have read assembly by hand, and a tool has existed for twenty
years that turns assembly into readable C in one click. Today you get it.

The delay was not asceticism. A decompiler produces fluent, plausible, confident
output, and it is sometimes wrong, and there is no way to detect which parts are
wrong except by reading the assembly underneath. A student who meets the decompiler
first learns to read its output. A student who meets it sixth learns to *check* its
output, because they already know what the underlying evidence looks like.

That distinction is the whole point of the course, and today it becomes explicit,
because the decompiler turns out to be the clearest possible illustration of it.

---

## 2. Disassembly is harder than it looks

The obvious belief is that turning bytes into instructions is a lookup: read the
opcode, consult the table, emit the mnemonic. For a single instruction, that is
true. For a whole binary, it is not, and the reason is that you must first know
**where the instructions start**.

x86 instructions are variable-length, from 1 to 15 bytes. Start decoding at the
wrong offset and you get a valid but entirely different instruction stream. There
is no marker in the bytes saying "an instruction begins here."

Two strategies exist.

**Linear sweep** decodes from the start of `.text` to the end, one instruction after
another. Fast and complete. It breaks the moment non-instruction data appears inside
the code section — a jump table, an inlined constant, alignment padding. The
disassembler decodes the data as instructions, produces garbage, and worse,
desynchronises: because lengths are variable, it may take several instructions to
resynchronise with the real stream, if it ever does.

**Recursive descent** starts at known entry points and follows control flow, marking
as code only what it can reach. Much more accurate about what is really code. But
Lecture 3 gave you the problem: `jmp rax`. When a jump target is computed at
runtime, the disassembler cannot know where it goes, so the code beyond it is never
reached and never disassembled.

Real tools combine both, add heuristics — function prologue patterns, alignment
conventions, symbol tables where available — and produce very good results. They are
still heuristics.

**Distinguishing code from data in an arbitrary stripped binary is undecidable in
general.** Not merely difficult: provably impossible, by reduction to the halting
problem. Every disassembler you will ever use is making educated guesses, and Ghidra
guesses very well, and it is still guessing.

This is failure mode zero, underneath everything else today.

---

## 3. What a decompiler actually does

The pipeline, which is worth drawing next to Lecture 1's compilation pipeline
because it is deliberately its mirror image:

```
machine code ─▶ disassemble ─▶ lift to IR ─▶ dataflow analysis ─▶ structure ─▶ C-like output
                 (guess           (normalise    (recover types      (recover
                  code/data)       the ISA)      and variables)      loops, if/else)
```

**Disassemble** — §2. Already a guess.

**Lift to IR** — translate each instruction into a simple intermediate language, so
that the rest of the analysis does not need to know about x86 specifically. This
stage is the most reliable; instruction semantics are well defined.

**Dataflow analysis** — determine which registers and stack slots constitute
"variables", track values through the function, and infer types from how values are
used. This is where Lectures 4 and 5 are being done automatically: argument
recovery, type inference, struct layout.

**Structuring** — take the control flow graph and fit it back into `if`/`while`/`for`
shapes. This is Lecture 3 in reverse, and it does not always succeed; when the graph
does not fit the available structures, you get `goto`s.

Now look at that diagram again. It is the compilation pipeline run backwards, and by
Lecture 1, the information was **destroyed**. Every backwards arrow is an inference.
The decompiler cannot un-destroy anything. It produces the *most likely* source
consistent with the machine code.

Most likely is not actual.

---

## 4. The six failure modes

Worth knowing by name, because recognising which one you are looking at tells you
what to check.

1. **Wrong types.** `int` where a pointer belongs, unsigned where the code is signed.
   Shows up as arithmetic that makes no sense, or comparisons that look inverted.
2. **Invented variables.** The decompiler names things `uVar3`, `local_28`,
   `undefined4`. Some correspond to real program variables; some are artefacts of
   how it split up registers and stack slots.
3. **Dropped side effects.** A flag set, a global touched, a value left in a register
   deliberately — things that do not fit the C model may be silently omitted.
4. **Mis-structured or mis-bounded loops.** Lecture 3's off-by-one, now produced
   automatically. Also mis-nesting, and `goto` soup where structuring failed.
5. **Wrong calling convention.** If a function does not follow the ABI — hand-written
   assembly, a compiler-internal helper — the decompiler reads arguments from the
   wrong registers and produces a confident, wrong signature.
6. **Missed indirect calls.** A `call rax` has no visible target, so the call graph
   is missing an edge. Whole regions of the program can appear unreachable.

None of this means decompilers are bad. They are among the best tools in the field
and they will save you enormous amounts of time. It means they are **generators**,
and generators are things you verify.

---

## 5. Navigating by cross-reference

The single most important habit when using a disassembler: **do not scroll.**

A binary has thousands of functions. Reading them in address order is the reverse
engineering equivalent of reading a dictionary front to back. The professional
technique is to start from something you care about and follow references to it.

A **cross-reference** (xref) is a record of "this location is referred to from these
other locations". Ghidra computes them during analysis, and they are how you move
around:

- You see the string `"invalid licence"` in `.rodata`. Who references it? One
  function — the one that prints it. Go there.
- That function is called from two places. Go to those. One of them is the licence
  check.
- The licence check reads a global. Who else touches that global? The code that
  sets it up.

In under a minute you are at the code that matters, in a binary you have never seen,
without reading anything irrelevant. This is triage, and Lecture 9 makes a method of
it.

Cross-references run both ways and both are useful: *references to* a location tells
you who uses this, *references from* tells you what this uses.

---

## 6. Renaming and retyping is recording hypotheses

When you work out that `param_1` is a `char *`, tell the tool. When you work out
that `FUN_00401180` parses the config, rename it.

This is not tidying up. Three things happen.

**The decompiler improves its output.** Type information propagates. Telling it that
a parameter is `struct aura_config *` turns `*(int *)(param_1 + 0x18)` into
`cfg->checksum` — and does so everywhere that pointer flows. Output that was
unreadable becomes readable because you supplied the one fact it could not infer.

**You stop re-deriving.** A binary has more functions than you can hold in your head.
A named, commented function is a conclusion you do not have to reach twice.

**Your reasoning becomes reviewable.** The annotations are your hypothesis log in
the tool. Someone else — or you in three weeks — can see what you concluded and,
crucially, disagree with it.

The correct relationship is worth stating explicitly, because it is the same
relationship you want with any assistant: **you supply the ground truth, the tool
does the bookkeeping.** You determined the struct layout by reading offsets. The
tool applies that determination consistently across ten thousand lines, which is
work you should never do by hand.

---

## 7. The thing neither tool can do

Consider a function named `check_license` that looks like this in the decompiler:

```c
int check_license(char *key) {
    return 1;
}
```

The decompiler is correct. That function does return 1.

Now cross-reference it. It is called once, and **its return value is discarded.** The
actual licence validation is inlined into the caller, computed from a rolling hash
over the key bytes, and compared against a value derived from the config.

`check_license` is a decoy.

Notice what happened. The decompiler did not lie — it accurately reported a true
property of the bytes. Asked "how does licensing work here?", a language model will
read that function and describe it fluently and confidently, and it will also be
reporting a true property of the bytes.

Both are wrong about the program, and neither is wrong about the code.

The missing thing is **intent**. "This function is bait" is not a property of the
bytes; it is a property of the whole program in the context of what someone was
trying to achieve. No amount of local analysis recovers it. It came from noticing
that the return value went nowhere, and asking why anyone would write a function
whose result is ignored.

That question — *why would someone write it this way?* — is the part of reverse
engineering that does not automate, because it is not a question about code. It is a
question about people.

---

## 8. Generators and evidence

The organising idea of the course, now statable precisely.

| | The disassembly + the running program | The decompiler | A language model |
|---|---|---|---|
| What it is | the bytes; ground truth | plausible C | fluent prose |
| Kind of thing | **evidence** | **generator** | **generator** |
| Can be wrong | no — it is what the machine does | yes, quietly | yes, quietly |

The decompiler and the model are the same species of thing. Both consume a program
and emit a likely interpretation. Both are fast, both are usually right, both are
confidently wrong in the specific places where the program departs from typical.

There is exactly one source of truth available, and it is the bytes plus their
behaviour when executed.

So the workflow is: **run the generators to save time, then check them against
evidence.** The checking is possible only because you can read the evidence, which
is the thing five lectures were spent on.

That is the answer to "why did you make me wait for the decompiler." A tool that
produces confident plausible output is dangerous to someone who cannot check it and
enormously powerful to someone who can. The five lectures made you the second kind
of person.

---

## 9. The honest counterweight

It would be easy to leave this lecture believing that decompilers are traps and
hand-reading is virtuous. That conclusion is as wrong as the one it replaces, and
worth correcting directly.

The decompiler just converted two hundred lines of assembly into readable C in about
one second, correctly, for roughly ninety-five percent of the functions in this
binary. Doing that by hand would take you a day. A model will rename forty variables
sensibly, summarise a large unfamiliar codebase, recognise a standard algorithm from
its constants, and write the tooling script you need, faster than anyone in the room.

These are not consolation prizes. They are genuinely large multipliers on your
effectiveness, and refusing to use them is not rigour, it is waste.

The claim is narrow and specific: **the last five percent is where the answer usually
hides.** The decoy, the custom constant, the misread signedness, the dropped
padding — these are not evenly distributed through the program. They cluster exactly
where someone was doing something interesting, which is exactly where you are
looking.

Use the tools for the ninety-five percent. Be the person who handles the five.

---

## Summary

- Distinguishing code from data in a stripped binary is undecidable in general. Every
  disassembler is guessing, well.
- Linear sweep desynchronises on embedded data; recursive descent misses everything
  behind an indirect jump.
- A decompiler is the compilation pipeline run backwards, and every backwards arrow
  is an inference over destroyed information.
- Six failure modes: wrong types, invented variables, dropped side effects,
  mis-structured loops, wrong calling convention, missed indirect calls.
- Navigate by cross-reference, not by scrolling. Start from a string or an import and
  follow references to the code that matters.
- Renaming and retyping records hypotheses, improves the tool's output, and makes
  your reasoning reviewable. You supply ground truth; the tool does bookkeeping.
- Neither a decompiler nor a model can represent **intent**. A decoy function is a
  true fact about the bytes and a lie about the program.
- Decompiler and model are both **generators**. The bytes and the running program are
  **evidence**. Run generators for speed; settle questions with evidence.
- The tools are genuinely excellent for ~95% of the work. The remaining 5% is where
  the answer usually is.

## Reading

- *The Ghidra Book*, chapters 1–5 — skim for the tool, read for the workflow.
- Exercise worth doing: decompile a program **you wrote yourself**. Find the first
  thing Ghidra gets wrong about code whose ground truth you already know. It is
  far more convincing than being told.
