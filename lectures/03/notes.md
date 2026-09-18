# Lecture 3 — Control flow: decisions and loops in machine code

---

## 1. The vocabulary problem

The machine has no `if`, no `while`, no `for`, no `switch`. It has one mechanism:
conditionally write a new value into `rip`. Every control structure you have ever
written is compiled into some arrangement of comparisons and jumps.

That sounds like a loss of information, and it is, but only partially. The compiler
does not invent a new arrangement each time. It has a small, finite vocabulary of
patterns — a handful of shapes it emits for each source construct. Learn the
vocabulary and you can read it backwards, not by decoding instructions one at a
time but by recognising shapes.

This lecture is that vocabulary.

---

## 2. Conditional jumps

Lecture 2 established that `cmp a, b` computes `a - b` and keeps only the flags.
The conditional jump instructions read those flags.

| After `cmp a, b` | Jump | Taken when |
|---|---|---|
| | `je` / `jz` | `a == b` |
| | `jne` / `jnz` | `a != b` |
| **signed** | `jl`, `jle`, `jg`, `jge` | `a < b`, `≤`, `>`, `≥` |
| **unsigned** | `jb`, `jbe`, `ja`, `jae` | `a < b`, `≤`, `>`, `≥` |

The mnemonics are worth decoding once so you stop mixing them up: signed
comparisons use **l**ess and **g**reater; unsigned comparisons use **b**elow and
**a**bove.

The important observation is that **signed and unsigned comparisons use different
instructions.** Comparing two integers for "less than" emits `jl` if they are
signed and `jb` if they are unsigned. The compiler had to choose, and its choice
records the signedness of a variable whose type was destroyed.

This is the same leverage as `movzx`/`movsx` in Lecture 2, and it is worth
collecting these as they accumulate. Each one is a small recovery of a type the
compiler erased.

---

## 3. The compiler branches on the negation

This is the single most common source of misreading, and it is worth stating
flatly before any examples.

Source code says what to do **when the condition holds**:

```c
if (x > 5) {
    do_something();
}
```

Machine code is organised around jumping **away when it does not**:

```asm
    cmp  DWORD PTR [rbp-4], 5
    jle  .Lskip                  ; x <= 5, so skip the body
    call do_something
.Lskip:
```

The source said `>`. The assembly says `jle`, which is `≤`. These are not in
conflict — the jump implements "get me out of here if the condition failed."

If you read `jle` and think "the source said less-or-equal", you have the program
inverted, and every conclusion downstream will be backwards. Read a conditional
jump as **the exit condition**, not the source condition.

---

## 4. Basic blocks and the control flow graph

A **basic block** is a maximal straight-line sequence of instructions with one
entry point and one exit. Blocks end at any jump, and begin at any jump target.

Splitting a function into basic blocks and drawing the edges between them gives you
the **control flow graph**, and this is the correct unit of reading. The
instructions inside a block are rarely the interesting part; the shape of the graph
is.

```
        ┌──────────┐
        │   B0     │  cmp / jle ──┐
        └────┬─────┘              │
             │ fall through       │
        ┌────▼─────┐              │
        │   B1     │              │
        └────┬─────┘              │
             └────────────▶┌──────▼───┐
                           │   B2     │
                           └──────────┘
```

That diagram is an `if` without an `else`: a test, a body, and a join point. You
can identify it as such without reading a single instruction inside `B1`.

Moving from reading instructions to reading blocks is the largest single
improvement in speed available to you, and it costs nothing but the habit. Lecture
2's line-by-line annotation exercise was the last time you should read that way.

---

## 5. The shapes

Six patterns cover the overwhelming majority of compiled control flow.

**`if` without `else`** — test, jump over the body.

```asm
    cmp  eax, 5
    jle  .Lend
    <body>
.Lend:
```

**`if`/`else`** — test, jump to the else branch; the if-branch ends with an
unconditional jump over it.

```asm
    cmp  eax, 5
    jle  .Lelse
    <if body>
    jmp  .Lend
.Lelse:
    <else body>
.Lend:
```

The unconditional `jmp` at the end of the first body is the tell. Without it, you
have an `if` with no `else`.

**`while`** — the test is placed at the *bottom*, with a jump into it at the top.

```asm
    jmp  .Ltest
.Lbody:
    <body>
.Ltest:
    cmp  eax, ebx
    jl   .Lbody
```

This looks inside out and there is a good reason for it: with the test at the
bottom, each iteration costs one conditional jump rather than a conditional jump
plus an unconditional one. The cost is a single extra jump on entry.

**`for`** — the `while` shape with an initialiser before it and the increment at the
end of the body. There is no separate `for` construct in machine code; a `for` loop
*is* a `while` loop with bookkeeping.

**`do`/`while`** — body first, test at the bottom, jump back.

```asm
.Lbody:
    <body>
    cmp  eax, ebx
    jl   .Lbody
```

Note what distinguishes this from `while`: there is **no jump at the top**. That
absence is the whole signature. A `while` loop enters by jumping to its test; a
`do`/`while` falls straight into its body because it must execute at least once.

**The ternary, and `cmov`** — this one has no branch at all.

```c
int max(int a, int b) { return a > b ? a : b; }
```

```asm
    cmp   edi, esi
    mov   eax, esi
    cmovg eax, edi        ; if edi > esi, eax = edi
    ret
```

`cmovg` is a conditional move: it writes the source to the destination only if the
condition holds, and it does so without branching. Compilers emit these because a
mispredicted branch costs far more than an always-executed move.

The consequence for you is significant: **a decision in the program can have no
jump in the machine code.** If you locate control flow by searching for jumps, you
will miss it entirely. Conditional moves are also why constant-time cryptographic
code is written the way it is — no branch means no timing difference that depends
on the secret.

---

## 6. Short-circuit evaluation

C guarantees that `&&` and `||` stop evaluating as soon as the answer is
determined. That guarantee is visible in the compiled code as multiple compares
with jumps to a common target.

```c
if (p != NULL && p->count > 0) { ... }
```

```asm
    test rdi, rdi
    je   .Lskip              ; p == NULL → skip, do NOT evaluate the second test
    cmp  DWORD PTR [rdi+8], 0
    jle  .Lskip              ; count <= 0 → skip
    <body>
.Lskip:
```

Two separate tests, both jumping to the same label. The pattern for `||` is the
mirror image: each test jumps *into* the body on success.

Recognising this matters because the second condition is only reachable through the
first. When you are reasoning about whether a dangerous piece of code can be
reached, the chain of short-circuit tests is the set of conditions that must all
hold.

---

## 7. `switch`

A `switch` has three common compilations, and which one you get depends on the case
values.

**Dense cases become a jump table.** If the values are close together — 0 to 20, say
— the compiler builds a table of addresses and indexes into it. This is the pattern
that appears in the worked example below.

**Sparse cases become an if-chain.** For values like 1, 900, 40000 a table would be
mostly empty, so the compiler emits sequential comparisons instead. This is
indistinguishable from a chain of `if`/`else if` in the source, and you should not
claim to know which the programmer wrote.

**Many sparse cases become a binary search.** With enough scattered values, the
compiler generates a tree of comparisons that halves the range each time.

The practical consequence is that "I found a jump table" tells you the case values
were dense, and "I found an if-chain" tells you nothing about whether the source
used `switch` or `if`. Information about which construct the programmer typed is
among the things compilation destroys.

---

## 8. The jump table in detail

This is the pattern worth being able to read cold, because it is how command
dispatchers, state machines, and protocol handlers are usually built.

```asm
    cmp  edi, 0x63
    ja   .Ldefault              ; bounds check — unsigned, so also catches negatives
    mov  eax, edi
    lea  rdx, [rip+0x1e4c]      ; address of the table
    movsx rax, DWORD PTR [rdx+rax*4]   ; table entry: a 4-byte SIGNED offset
    add  rax, rdx               ; offset + table base = target address
    jmp  rax                    ; indirect jump
```

Reading it line by line:

The `cmp` and `ja` are a **bounds check**. Note that it is unsigned: a negative
index reinterpreted as unsigned becomes enormous and fails the check too, so one
comparison handles both ends. This is why compilers use unsigned comparisons for
bounds checking, and recognising the idiom is useful.

The `lea` computes the table's address, RIP-relative (Lecture 2 — and remember the
offset is from the *next* instruction).

The table does not contain addresses. It contains **32-bit signed offsets** from
the table's own base. This keeps the table half the size of one holding full
64-bit addresses, and it makes the code position-independent. `movsx` sign-extends
the offset, which is necessary because targets can lie before the table.

`add` reconstructs the absolute address and `jmp rax` transfers control.

Two things follow. First, the bounds check is the entire safety of this
construction: if it is missing or wrong, the program indexes past the end of the
table and jumps to whatever it finds. That is a serious class of vulnerability, and
you can now recognise its absence. Second, to enumerate the possible targets you
read the table — which means knowing where it starts, how wide the entries are, and
how many there are. All three are recoverable from the instructions above.

---

## 9. Loops under optimisation

At `-O2` loops are transformed in ways that obscure the original structure. The
transformations are standard and worth recognising.

**Strength reduction.** A loop indexing `arr[i]` needs `base + i*4` each iteration.
The compiler often replaces the multiply with a pointer that it increments by 4,
eliminating the arithmetic. The `*4` disappears from the addressing mode, and with
it the direct clue about element size.

**Induction variable elimination.** If `i` is only used to compute an address, the
compiler may delete `i` entirely and loop on the pointer, comparing it against an
end pointer. The loop counter you expect to find does not exist.

**Unrolling.** The body is duplicated several times per iteration to reduce branch
overhead. A loop that looks like it processes four elements per pass may be
processing one, four times over.

**Rotation.** The loop is restructured so the test moves, which changes which shape
from §5 it resembles.

The reason to know these is to avoid a specific error: concluding that a loop
processes four items because you see four copies of the body, or that there is no
loop counter because you cannot find one. The behaviour is preserved; the structure
is not.

---

## 10. Where automated reconstruction goes wrong

Reconstructing source from control flow is precisely the task at which automated
tools are simultaneously most useful and most quietly unreliable.

The useful part is real: given a function's disassembly, a decompiler or a model
will produce readable C with the loops and conditionals in roughly the right
places, in a second, and it will usually be right.

The failure mode is narrow and specific: **loop bounds.**

Consider a loop whose test is `jle` — a `≤` comparison, so the loop body runs `n+1`
times. The overwhelmingly common idiom in real code is `<`, running `n` times. A
tool producing the most likely reconstruction will emit `i < n`. The result
compiles, reads naturally, and is wrong by one iteration.

Nothing about that output looks suspicious. It is not garbled or hedged. It is a
perfectly ordinary loop, and the difference between it and the truth is one
character in the disassembly.

The check is mechanical. Set a breakpoint on the loop body, run with a known input,
and count the hits. If `n` is 5 and the breakpoint fires six times, the bound is
`≤`. This takes about thirty seconds and requires nothing beyond the ability to
find the body.

It is worth noticing that off-by-one errors in loop bounds are, historically, among
the most productive sources of security vulnerabilities in real software. The
difference between `<` and `≤` is the difference between writing inside a buffer
and writing one element past it. Getting that boundary exactly right is not
pedantry.

---

## Summary

- The machine has one mechanism: conditionally write to `rip`. Every control
  structure compiles to arrangements of compares and jumps.
- Signed and unsigned comparisons use different jump instructions, which recovers a
  type the compiler erased.
- **The compiler branches on the negation.** Read a conditional jump as the exit
  condition, not the source condition.
- Read in basic blocks, not instructions. The shape of the graph is the information.
- Six shapes cover almost everything. A `do`/`while` is identified by the *absence*
  of a jump at the top.
- `cmov` means a decision can exist with no jump at all.
- A jump table's bounds check is the entire safety of the construction. Its entries
  are usually signed offsets from the table base, not addresses.
- At `-O2`, loops are rotated, unrolled, and stripped of counters. Behaviour is
  preserved; structure is not.
- Automated reconstruction is reliable on shape and unreliable on **bounds**. Check
  by counting iterations.

## Reading

- *Computer Systems: A Programmer's Perspective*, §3.6 — control flow in full.
- Exercise worth doing: write a `switch` with ten dense cases, compile at `-O0` and
  `-O2`, then spread the case values out and watch the jump table become an
  if-chain.
