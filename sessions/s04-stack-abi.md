# Session 4 — The stack, calling conventions, and functions

**The one idea:** a function call is a *convention*, not a language feature. Once
you know the convention, every function announces its own signature in the way it
touches registers and the stack.

---

## Outcomes

1. Draw a stack frame and explain what `push`, `pop`, `call`, `ret` do to `rsp`.
2. State the System V AMD64 argument order and return register from memory.
3. Recover a function's arity and rough argument types from register liveness.
4. Distinguish callee-saved from caller-saved registers and use that to find
   frame boundaries.
5. Explain, concretely, what "overwriting the return address" does — and why it
   is a whole subfield they are not doing yet.
6. Verify a model's claimed function signature against register-use evidence.

> **Expect to run long.** This session is dense and the return-address demo is
> irresistible to a good room. Pre-plan your cuts (see notes).

---

## Prep checklist

- [ ] `s04/` pack: `frames`, `fact` (recursive), `sigs` (6 unknown functions),
      `redzone`, `retaddr` (the demo binary, no stack protector — see build plan)
- [ ] Reference card **#3 (SysV ABI)** printed — issue at the start today
- [ ] Big stack diagram space on the board, growing *downward*
- [ ] gdb, `x/20gx $rsp` muscle-memory rehearsed
- [ ] Casts: `s04-demo1.cast` (recursion), `s04-demo2.cast` (retaddr)

---

## 0:00 — Warm-up (15 min)

Five questions:

1. Split this 6-instruction snippet into basic blocks. *(on screen)*
2. Source said `if (x >= 10)`. What jump do you expect, and why the "opposite"?
3. What does `test rax, rax; je` check?
4. From the AURA-7 map on the board: how many commands did we find, and how was
   the dispatch done?
5. `cmov` — what is it and why might a decision have no jump?

Settle Q1 live. Q4 points at the standing board — the AURA-7 map grew last
session and will grow again today.

---

## 0:15 — Cold open (10 min)

On screen, a stripped function, no name, no context:

```asm
sub_401180:
  push rbp
  mov  rbp, rsp
  mov  DWORD PTR [rbp-0x14], edi
  mov  QWORD PTR [rbp-0x20], rsi
  ...
  mov  eax, ...
  leave
  ret
```

**Question:** how many arguments does this function take, and what are their
types? You may not run it. You may only read it.

Written prediction. Give them the ABI card now and say "the answer is on this
card if you know how to read it." Resolved through the whole session; formally at
2:55.

---

## 0:25 — Teach A: the stack and the call (35 min)

### A1 — What the stack *is* (10 min)

Draw it on the board, addresses **decreasing upward**, and grow it live all
session:

```
  high addresses
  ┌────────────────────┐
  │  caller's frame    │
  ├────────────────────┤ ◀── rbp (frame base)
  │  saved rbp         │
  │  return address    │  ◀── put here by `call`
  │  local a  [rbp-8]  │
  │  local b  [rbp-16] │
  └────────────────────┘ ◀── rsp (top of stack)
  low addresses            (grows downward)
```

The four operations, each demonstrated live in gdb with `x/4gx $rsp` before and
after:

```
push rax   ≡   sub rsp, 8 ; mov [rsp], rax
pop  rax   ≡   mov rax, [rsp] ; add rsp, 8
call f     ≡   push (address of next instr) ; jmp f
ret        ≡   pop rip
```

> "`call` pushes the return address. `ret` pops it back into `rip`. That's the
> whole mechanism. Which means the return address is *just data on the stack* —
> and if you can write to it, you control where the function returns. Hold that
> thought for ninety minutes."

### A2 — The convention (13 min)

Reference card #3, on the board, drilled:

```
 Integer/pointer args:  rdi  rsi  rdx  rcx  r8  r9   then stack
 Return value:          rax  (rdx:rax for 128-bit)
 Callee-saved:          rbx  rbp  r12  r13  r14  r15  (function must preserve)
 Caller-saved:          rax  rcx  rdx  rsi  rdi  r8-r11 (may be clobbered)
 Stack alignment:       16-byte at the point of `call`
 Red zone:              128 bytes below rsp, usable without adjusting rsp
```

Why each fact is a *tool*, not trivia:

- **Argument registers** → a function that reads `rdi`, `rsi`, `rdx` before
  writing them takes (at least) three arguments. The reads announce the arity.
- **Return register** → whatever is in `rax` at `ret` is the return value; if
  nothing meaningful is, it's `void`.
- **Callee-saved** → a prologue that pushes `rbx`, `r12` tells you the function
  intends to use them across calls — a hint about its internal complexity.

> "You recover a signature by watching which argument registers are read *before*
> they're written. Read-before-write means 'the caller gave me this.' That's not
> a heuristic — it's what the convention *guarantees*. The compiler had no choice.
> Your leverage in RE is always the thing the compiler had no choice about."

### A3 — Prologue, epilogue, locals, and their absence (12 min)

The `-O0` frame: `push rbp; mov rbp, rsp; sub rsp, N` … `leave; ret`. Locals
addressed off `rbp`.

Then break it, live, because real code is `-O2`:

- **Frame pointer omission** — `-O2` often drops `rbp` and addresses everything
  off `rsp`. No tidy frame base. Show it.
- **The red zone** — a leaf function scribbling in `[rsp-8]` *without* a `sub rsp`.
  Show `redzone`. "It looks like it's writing past the top of the stack. It's
  allowed. 128 bytes. Know it exists or it'll confuse you for an hour."
- **Tail calls** — `jmp` to another function instead of `call`+`ret`. "A `jmp`
  at the end of a function, to another function, is a call that reused the frame.
  Don't read it as spaghetti."

> "At `-O2` the tidy textbook frame is gone. But the *convention* is not
> negotiable — arguments still arrive in `rdi`, `rsi`, `rdx`. The frame is a
> convenience the compiler can drop. The ABI is a contract it cannot. Lean on the
> contract."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: signatures from silence (40 min)

Full spec: [`labs/s04-lab.md`](../labs/s04-lab.md).

- **Core** — for `sigs`' 6 stripped functions, give the arity of each, justified
  by which argument registers are read before written.
- **Stretch** — add argument *types* where the code reveals them: `[rdi+rsi*4]`
  says `rdi` is a pointer to 4-byte elements and `rsi` is an index; a `movss`
  says float; an 8-bit compare says `char`. Return type from `rax` usage.
- **Boss** — one function in `sigs` uses a **non-standard calling convention**
  (hand-written asm, args in the wrong registers). Find it and explain how you
  know it's not following SysV. (Explain-back — this one is the AI-hostile
  artifact and the drill hinges on it.)

Circulate. The move to reward: a student who says "it reads `rdx` before writing
it, so it's at least the third argument." That sentence is the entire skill.

---

## 1:50 — Teach B: live demo — recursion, then the dangerous ninety seconds (25 min)

**Part 1 — recursion (14 min).** `fact`, a recursive factorial. Break on entry,
`x/20gx $rsp`, and **draw each frame on the board as it's pushed.** Step into the
recursion three levels deep; the board fills with stacked frames; then step out
and watch them pop and `rax` carry the product back up.

> "Recursion isn't magic and it isn't a language feature. It's the same frame
> pushed several times. The stack *is* the recursion. When you can see the
> frames, recursion stops being scary forever."

**Part 2 — the return address (9 min).** The one memory-safety moment in the
course. `retaddr`, built with no stack protector.

Find the saved return address on the stack. Overwrite it in gdb:

```
(gdb) x/gx $rbp+8        # the saved return address
(gdb) set {long}($rbp+8) = <address of secret_function>
(gdb) continue
```

Control lands in a function that was never called.

> "I changed one 8-byte value in memory and the program returned somewhere it was
> never supposed to go. I didn't exploit a bug — I just wrote to the stack in a
> debugger. But now imagine the *program* writes past the end of a buffer that
> happens to sit right below this return address. Same effect, no debugger. That
> is the buffer overflow, and it is the foundation of an entire field.
>
> We are not doing that field in this course. But you now know *why* memory
> layout is a security property and not just an implementation detail. When you
> hear 'stack canary' or 'ASLR' — S7 — this is what they're defending."

Point onward (pwn.college, the S10 resource map) and stop. Do not tumble down the
exploitation rabbit hole; it eats the rest of the session and it is not the
course.

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: AURA-7 handler signatures (30 min)

Students take three command handlers found in S3 and recover each signature:
arity, argument types where visible, return type. Add these to the standing
AURA-7 MAP on the board.

Required: for each handler, one sentence of the form *"handler 0x12 takes
(char *config_path, int flags) and returns int — because it reads `rdi` as a
pointer passed to `strlen`, reads `esi` and `and`s it with a mask, and `rax`
holds a small integer at `ret`."* Evidence, then conclusion. Always that order.

Seed the drill: **"ask a model for the signature of one handler. Keep its
answer."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** Model output on a handler: *"`int handler(char *s)` — takes a
single string argument."*

1. *State it.* One argument, a string.
2. *What would falsify it?* — if there's a second argument, some code reads `rsi`
   before writing it. So: does anything read `rsi` early? Get this from the room.
3. *Observe.* `objdump`/gdb: `rsi` is read at the third instruction, before any
   write. Two arguments, not one.
4. *Verdict.* **Wrong — missed an argument.** Reason: the model latched onto the
   `strlen(rdi)` call, concluded "string function, takes a string", and stopped
   looking. It reasoned from the *first* familiar thing, not from register
   liveness across the whole function.

> "This is the argument-register version of the loop bound from last session.
> The model saw something it recognised and stopped reading. You caught it by
> doing the one thing the convention *guarantees* will work: read-before-write
> means it came from the caller. The ABI can't lie. Models can."

**Cold-open reveal.** Return to `sub_401180`: reads `edi` (→ `[rbp-0x14]`, 4-byte,
an `int`) and `rsi` (→ `[rbp-0x20]`, 8-byte, a pointer). Two arguments:
`int` and a pointer. `rax` set before `leave` → returns an `int`. Signature
recovered from silence, no execution.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 4 | AURA-7 handler is `int f(char *s)` — one argument | ✗ Wrong (missed arg) | `rsi` read before write ⇒ ≥2 args. Model stopped at the recognisable `strlen(rdi)` and never checked the rest of the register liveness |

---

## Lecturer notes

**The single biggest time sink is the retaddr demo.** It is thrilling and
students will want to go further. Budget it at nine minutes, hard. If the room is
hot, that is what the S10 resource map and pwn.college pointer are *for* — send
them there, don't teach it now.

**Frame-pointer omission blindsides students.** At `-O2` there is no `rbp` frame
and they panic. Pre-empt: show an FPO function in A3 and say "when you can't find
the frame base, everything is off `rsp` and the frame size is the `sub rsp, N` at
the top." Put it on the card.

**Argument types are genuinely hard and partly guesswork.** Be honest: arity is
usually *certain* from register liveness; types are often *likely*, not certain.
Reinforce the confidence column from S3. Do not let students overclaim a type
they merely suspect — that overclaiming is precisely the failure mode the drill
punishes.

**Running long (you will).** Cut in this order: Lab A Boss tier (but the
non-standard-convention function is the drill's setup elsewhere — if you cut it
from the lab, still *show* it in 60 seconds), then the tail-call and red-zone bits
of A3. Protect the recursion demo and the ABI card drill above all.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-4)

- **Read:** CS:APP §3.7 (30 min) — procedures and the stack.
- **Do:** write a 3-argument function, compile `-O0`/`-O2`, and confirm the args
  arrive in `rdi`/`rsi`/`rdx` in both; find where they live in each build.
- **Crackme:** crackmes.one difficulty 2, any with multiple functions.
- **Self-check:** 5 questions, answers included.
