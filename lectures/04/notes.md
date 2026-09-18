# Lecture 4 — The stack, calling conventions, and functions

---

## 1. A function call is a convention

The processor has no concept of a function. It has `call` and `ret`, which are
jumps that remember where they came from, and it has a register conventionally used
as a stack pointer. Everything else you associate with functions — arguments,
return values, local variables, scope — is an **agreement** between the compiler
and everyone it must interoperate with.

That agreement is called an Application Binary Interface. On 64-bit Linux it is the
System V AMD64 ABI, and it is documented, fixed, and mandatory for any code that
wants to call or be called by anything else.

This is the most useful fact in the course so far. The compiler had *no choice*
about it. Arguments go in specific registers because otherwise the callee cannot
find them. That constraint means a stripped function, with no symbols and no
debugging information, still announces its own signature in the way it touches
registers. You just have to read it.

---

## 2. What the stack actually is

The stack is a region of memory. `rsp` holds the address of its top. There is
nothing more to it than that — no special hardware structure, no protection, no
type.

By convention on x86-64 the stack **grows downward**: pushing decreases `rsp`.
This is historical and universal, and it produces the diagram you will draw for the
rest of the course:

```
  high addresses
  ┌────────────────────┐
  │  caller's frame    │
  ├────────────────────┤
  │  return address    │  ← placed here by `call`
  │  saved rbp         │  ← rbp points here
  │  local a  [rbp-8]  │
  │  local b  [rbp-16] │
  └────────────────────┘  ← rsp (top of stack)
  low addresses
```

The four stack instructions are defined entirely in terms of `rsp`:

```
push rax   ≡   sub rsp, 8  ;  mov [rsp], rax
pop  rax   ≡   mov rax, [rsp]  ;  add rsp, 8
call f     ≡   push (address of the next instruction)  ;  jmp f
ret        ≡   pop rip
```

Read the last two again. `call` pushes the address it should come back to, then
jumps. `ret` pops that address into `rip`.

Which means **the return address is ordinary data sitting in memory**. Nothing
marks it as special. If something writes to that location, the function returns
somewhere else. We come back to this at the end of the lecture.

---

## 3. The System V AMD64 ABI

The parts you need:

```
Integer / pointer arguments, in order:
    rdi   rsi   rdx   rcx   r8   r9      then the stack
     1     2     3     4     5    6

Return value:        rax        (rdx:rax for 128-bit values)
Floating point:      xmm0-xmm7 for arguments, xmm0 for return

Callee-saved:        rbx  rbp  r12  r13  r14  r15
                     (a function must leave these as it found them)
Caller-saved:        rax  rcx  rdx  rsi  rdi  r8-r11
                     (may be destroyed by any call)

Stack alignment:     rsp must be 16-byte aligned at the point of a `call`
Red zone:            128 bytes below rsp, usable without adjusting rsp
```

There is no particular logic to the argument order — `rdi` before `rsi` is a
convention, not a deduction. Memorise it. It is on the reference card, it appears
in every function you will ever read, and it will be second nature within two
sessions.

The **callee-saved / caller-saved** split is worth understanding rather than
memorising. Some registers are guaranteed to survive a function call; the rest may
be destroyed. A function that wants to use a callee-saved register must save and
restore it, which is why prologues often begin with `push rbx`. That push is a
signal: the function intends to keep something alive across a call it is going to
make.

---

## 4. Recovering a signature from register use

Here is the technique this lecture exists to teach.

> **A register that is read before it is written was an incoming argument.**

If a function reads `rdx` before storing anything into it, the value must have come
from somewhere, and the only place it can have come from is the caller. By the ABI,
`rdx` is the third argument. Therefore the function takes at least three arguments.

Conversely, a register that is written before it is read is scratch space — a local,
not a parameter.

This is not a heuristic. It follows from the convention, and the convention was not
optional for the compiler.

Applying it to an unknown function:

```asm
sub_401180:
    push rbp
    mov  rbp, rsp
    mov  DWORD PTR [rbp-0x14], edi     ; edi read → arg 1, 4 bytes wide
    mov  QWORD PTR [rbp-0x20], rsi     ; rsi read → arg 2, 8 bytes wide
    ...
    mov  eax, ...                      ; something meaningful in eax
    leave
    ret
```

- `edi` is read and spilled to a 4-byte slot: argument 1 is a 4-byte integer.
- `rsi` is read and spilled to an 8-byte slot: argument 2 is 8 bytes — a pointer or
  a long.
- `rdx` is never read: there is no third argument.
- `eax` is set before `ret`: the function returns a 4-byte value.

Signature: `int sub_401180(int, void *)`, recovered without symbols, without
running the program, and without any tool beyond a disassembler.

**Arity is usually certain. Types are usually only likely.** An 8-byte argument
might be a pointer, a `long`, or a `size_t`. You find out by watching how it is
used: dereferenced means pointer, passed to `strlen` means `char *`, compared
against a small number means a count. Keep these distinct in your notes —
overclaiming a type you merely suspect is the failure this course works hardest to
prevent.

---

## 5. Prologue, epilogue, and locals

The classic `-O0` function frame:

```asm
    push rbp            ; save the caller's frame pointer
    mov  rbp, rsp       ; establish ours
    sub  rsp, 0x20      ; reserve 32 bytes for locals
    ...
    leave               ; ≡ mov rsp, rbp ; pop rbp
    ret
```

With `rbp` fixed for the duration of the call, every local has a stable address:
`[rbp-0x8]`, `[rbp-0x10]`, and so on. Arguments spilled to the stack appear here
too. The return address is always at `[rbp+8]`, and the caller's saved `rbp` at
`[rbp]`.

Reading a `-O0` function therefore reduces to building a table of what lives at each
offset. Do that first and the rest of the function becomes legible.

---

## 6. When the textbook frame is not there

Production code is `-O2`, and at `-O2` the tidy frame is frequently absent. Three
things to expect.

**Frame pointer omission.** `rbp` is a perfectly good general-purpose register, and
if the compiler can track offsets from `rsp` itself, it will use `rbp` for
something else. There is then no frame base, and locals are addressed as
`[rsp+0x8]`, `[rsp+0x10]`. The complication is that `rsp` moves during the function,
so the same local has different offsets at different points. When you cannot find a
frame base, look for the `sub rsp, N` at the top: `N` is the frame size.

**The red zone.** The 128 bytes *below* `rsp` are reserved for the current function
by the ABI. A leaf function — one that calls nothing — can use that space without
adjusting `rsp` at all. So you will see writes to `[rsp-8]` that look like they are
scribbling past the top of the stack. They are legal. Knowing this exists saves an
hour of confusion.

**Tail calls.** If the last thing a function does is call another function and
return its result, the compiler can replace `call`/`ret` with a plain `jmp`. The
second function reuses the first one's frame and returns directly to the original
caller. A `jmp` to another function at the end of a function is not spaghetti — it
is a call that avoided a stack frame.

---

## 7. Recursion

Recursion needs no special machinery. Each call pushes another frame; the stack
holds them all.

```asm
fact:
    push rbx
    mov  ebx, edi            ; keep n in a callee-saved register
    cmp  edi, 1
    jle  .Lbase
    lea  edi, [rbx-1]        ; n-1
    call fact                ; recurse
    imul eax, ebx            ; result *= n
    jmp  .Ldone
.Lbase:
    mov  eax, 1
.Ldone:
    pop  rbx
    ret
```

Note `rbx`. The function needs `n` after the recursive call returns, and `rdi` is
caller-saved — the recursive call is free to destroy it. So `n` goes into `rbx`,
which is callee-saved, and the prologue pushes it to honour that guarantee. The
`push rbx` at the top is not decoration; it is what makes the multiply at the
bottom correct.

Watching the stack while stepping through this is the fastest way to stop finding
recursion mysterious. There is no magic: there is the same frame layout, present
several times, each with its own `n`.

---

## 8. The return address is just data

Collecting two facts already established:

1. `call` pushes the return address onto the stack.
2. Local variables live on the stack, immediately adjacent to it.

Nothing distinguishes the return address from any other eight bytes. If a program
writes past the end of a local buffer, it will eventually write over the saved
return address, and when the function executes `ret`, control transfers to whatever
was written.

You can demonstrate this without any bug at all, in a debugger:

```
(gdb) x/gx $rbp+8                              # the saved return address
(gdb) set {long}($rbp+8) = 0x401196            # overwrite it
(gdb) continue
```

The program returns into a function that was never called.

That is the buffer overflow, and it is the foundation of an entire field. A program
that copies user input into a fixed-size stack buffer without checking the length
hands the attacker control of `rip`.

This course does not go further down that path. It is worth ninety seconds because
it converts "memory layout" from an implementation detail into a security property,
and because the defences you will hear about — stack canaries, non-executable
stacks, ASLR — are all responses to exactly this, and will make sense in Lecture 7
only if you have seen the thing they defend against.

---

## 9. What automated analysis misses here

Function signatures are a task where tools perform well on average and fail in a
consistent direction: **they under-count arguments.**

The mechanism is straightforward. A function begins by calling `strlen(rdi)`. That
is a strongly recognisable pattern — string function, takes a string — and the most
likely signature given that opening is `something f(char *)`. A tool that pattern-
matches on the recognisable opening and stops will report one argument.

Meanwhile `rsi` is read on the third instruction, before anything writes to it.
There are two arguments.

The failure is not a failure of reading. It is a failure to *keep* reading after
finding something familiar. And it is invisible in the output, because a plausible
one-argument signature looks exactly like a correct one-argument signature.

The check is the technique from §4, applied deliberately rather than impressionistically:
for each of `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`, in order, is it read before it
is written? That question has a definite answer, obtainable from the disassembly in
under a minute, and the ABI guarantees the answer is meaningful.

The general shape of this — the tool stopped at the first recognisable thing —
recurs. It is worth naming now, because you will see it again in Lectures 6, 8 and 9
in different costumes.

---

## Summary

- A function call is a convention, not a hardware feature. The ABI was mandatory for
  the compiler, which is why it is readable evidence for you.
- The stack is memory; `rsp` points at its top; it grows downward.
- `call` pushes a return address, `ret` pops it into `rip`. Nothing marks that
  address as special.
- Arguments: `rdi rsi rdx rcx r8 r9`. Return: `rax`. Callee-saved: `rbx rbp r12-r15`.
- **A register read before it is written was an incoming argument.** That is how you
  recover arity from a stripped function.
- Arity is usually certain; types are usually only likely. Record the difference.
- At `-O2` expect no frame pointer, use of the red zone, and tail calls. The ABI
  still holds.
- `push rbx` in a prologue means the function needs a value to survive a call it will
  make.
- Overwriting the saved return address redirects control. That is the buffer
  overflow, and the reason memory layout is a security property.
- Tools under-count arguments by stopping at the first recognisable call. Check
  read-before-write for all six registers.

## Reading

- *Computer Systems: A Programmer's Perspective*, §3.7 — procedures and the stack.
- Exercise: write a three-argument function, compile at `-O0` and `-O2`, and confirm
  the arguments arrive in `rdi`/`rsi`/`rdx` in both. Then find where each one lives
  in each build.
- If the return-address demonstration interested you, that path continues at
  pwn.college. It is a different course from this one.
