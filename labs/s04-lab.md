# Lab 4 — Signatures from silence

**Time:** 40 min · **Pack:** `s04/sigs` (6 stripped functions), reference card #3

---

## Core — Arity of six functions

For each of the six stripped functions in `sigs`, state **how many arguments** it
takes, justified by which argument registers (`rdi rsi rdx rcx r8 r9`) are **read
before being written**.

**Deliverable:** a table — function, arity, the register-liveness evidence.

| fn | arity | evidence |
|---|---|---|
| sub_1 | 2 | reads `rdi`, `rsi` before writing; never touches `rdx` |
| … | | |

### Solution outline

Built (BUILD-PLAN §S4) with arities 0,1,2,3,2,1 in some order. The read-before-
write rule is exact: a register read before any write to it was an incoming
argument. A register written first was a scratch local. Accept only answers that
cite the specific instruction.

### Watch for

- Counting a register that's written before it's read (that's a local, not an
  arg).
- Missing that a function using `rdx` takes *at least* three args (rdi, rsi, rdx).

---

## Stretch — Add types

For each function, add argument **types** where the code reveals them, and the
return type from `rax`:

- `[rdi + rsi*4]` → `rdi` is `int*`/array of 4-byte, `rsi` is an index
- `movss`/`movsd` → float/double
- 8-bit compare (`cmp al, …`) → `char`
- passed to `strlen`/`strcmp` → `char *`
- `rax` holds a small int at `ret` → returns `int`; nothing meaningful → `void`

**Deliverable:** best-effort signatures **with a confidence marker** (`certain` /
`likely` / `guess`) per type. Arity is usually certain; types often only likely.

### Solution outline

Provide the ground-truth signatures in the solutions repo. Grade the *confidence
calibration* as much as the answer: a student who marks a genuinely ambiguous type
`certain` is making the exact error the drill punishes.

---

## Boss — The impostor (explain-back)

One function in `sigs` uses a **non-standard calling convention** — hand-written
asm that takes its arguments in the wrong registers (e.g. `r10`, `r11`, or reads
args off the stack directly). Find it, and explain how you know it isn't following
SysV.

**Deliverable:** the function + the reasoning, to a neighbour, notes closed.

### Solution outline

This is the session's **AI-hostile artifact.** A model asked for its signature
will assume SysV and read the first args from `rdi`/`rsi` — producing a confident,
wrong signature. The tell: the function reads `r10`/`r11` (or `[rsp+N]`) before
writing them, while `rdi`/`rsi` are untouched or used as scratch. A student who
spots "it's reading `r10` before writing it, but SysV never passes args in `r10`"
has found it. This function is the setup for the S4 drill — even if you cut the
Boss tier for time, *show* this function in the last 60 seconds.

---

## TA notes

The sentence to reward all session: *"it reads `rdx` before writing it, so it's at
least the third argument."* That single move — read-before-write ⇒ incoming arg —
is the whole lab. The ABI is a contract the compiler couldn't break; that's your
leverage.
