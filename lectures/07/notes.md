# Lecture 7 — Dynamic analysis: running it and watching it

---

## 1. Two kinds of question

Everything so far has been **static analysis**: reading a program without running
it. Static analysis answers "what can this program do?" — it sees all the code,
including paths that rarely execute.

**Dynamic analysis** runs the program and observes it. It answers "what does this
program actually do, with this input, right now?" — concretely, with real values,
including things static analysis cannot reach: values computed at runtime, data read
from files, the result of an indirect call.

Neither replaces the other. Static analysis covers all paths with imprecise values;
dynamic analysis covers one path with exact values. Most real work alternates:
read until you have a hypothesis, run to test it, return to reading with what you
learned.

This lecture is about the running half, and about a discipline that goes with it —
that **a breakpoint is a hypothesis test and a patch is an experiment**, not a
victory.

---

## 2. What a running program is

You have not taken an operating systems course, so here is exactly what you need and
nothing more.

When the kernel runs your program it creates a **process** with its own **virtual
address space** — a private map of addresses to physical memory. Every process
believes it has the machine to itself. Addresses in one process mean nothing in
another.

That space contains the regions from Lecture 5, plus the libraries:

```
  0x7fff...  ┌──────────────┐  high
             │    stack     │  grows down   (Lecture 4 lives here)
             │      ↓       │
             │              │
             │   [libc]     │  mapped shared library
             │              │
             │      ↑       │
             │    heap      │  grows up     (malloc, Lecture 5)
             ├──────────────┤
             │ .bss  .data  │  globals
             │ .rodata      │  constants
             │ .text        │  your code
  0x400000   └──────────────┘  low
```

You can see the real thing:

```bash
cat /proc/<pid>/maps        # or, in gdb: info proc mappings
```

That output shows each mapped region, its permissions (`r-xp` for code, `rw-p` for
data), and which file it came from. It is the ground truth about what is loaded and
where, and it is the first thing to look at when an address does not make sense.

---

## 3. Syscalls: the boundary

Your code runs in **user mode**, where it cannot touch the disk, the network, or the
screen. Only the kernel can do those things. When your program needs one, it makes a
**system call**: it puts a call number in `rax`, arguments in `rdi`, `rsi`, `rdx`,
`r10`, `r8`, `r9`, and executes the `syscall` instruction, which traps into the
kernel.

```asm
    mov  eax, 1          ; syscall 1 = write
    mov  edi, 1          ; fd 1 = stdout
    mov  rsi, msg        ; buffer
    mov  edx, 13         ; length
    syscall
```

That is the entire user/kernel boundary. `printf` is not magic — it formats a string
in user space and eventually calls `write`. libc is a library of convenient wrappers
around these traps.

Two things follow. First, **the syscall boundary cannot be avoided**: a program that
reads a file must issue `openat` and `read`, however obfuscated the rest of it is.
That makes syscalls an excellent observation point. Second, syscall numbers are fixed
by the kernel ABI, so they survive everything compilation does.

---

## 4. ASLR

Modern systems randomise the load addresses of the stack, the heap, and shared
libraries on every run. **Address space layout randomisation** exists to make
Lecture 4's return-address attack harder: if you cannot predict where anything is,
you cannot reliably redirect control to it.

For you this has one practical consequence: **addresses differ between runs.** Your
stack address will not match your neighbour's, and neither will match the one from
ten minutes ago.

gdb disables ASLR by default so that debugging is reproducible. This is helpful and
occasionally misleading: an address that is stable under gdb will move when the
program runs normally. When you record an address in your notes, record whether it
was under gdb, and prefer *offsets from a known base* over absolute addresses.

---

## 5. How a breakpoint actually works

This is the fact that turns a debugger from magic into a mechanism.

You tell gdb to break at an address. gdb **overwrites the byte at that address with
`0xCC`** — the encoding of `int3`, a one-byte software interrupt instruction. Then
it lets the program run. When execution reaches that byte, the CPU traps into the
kernel, which stops the process and notifies gdb. gdb puts the *original* byte back,
so when you inspect the program it looks untouched, and restores the breakpoint when
you continue.

You can see it:

```
(gdb) x/1bx $pc          # before setting a breakpoint here
0x401136:  0x55
(gdb) break *0x401136
(gdb) x/1bx 0x401136     # ... while the program is running
0x401136:  0xcc
```

Two consequences matter.

**A program can detect this.** If it reads its own code and finds `0xCC` where it
expects something else, it knows it is being debugged. That is a standard
anti-debugging technique, and you now understand it completely rather than as a
mysterious trick.

**Hardware watchpoints are a different mechanism.** The CPU has debug registers that
hold a handful of addresses; it traps when any of them is read or written. No bytes
are patched. This is how you answer "what is writing to this variable?" — a question
that would otherwise require finding every possible writer by hand. The limitation
is that there are only four such registers, so you get four hardware watchpoints.

---

## 6. The gdb toolkit

The commands worth having in your fingers:

```
break f / b *0xADDR          set a breakpoint
break f if x == 5            conditional — only stop when it matters
tbreak                       temporary: fires once, then removes itself
watch  <expr>                stop when the value changes (hardware)
rwatch <expr>                stop when it is read

run / continue               start / resume
si / ni                      step one instruction / step over calls
finish                       run until the current function returns

info registers [reg]         register state
x/8gx  $rsp                  examine: 8 giant-words in hex
x/20i  $pc                   examine: 20 instructions
x/s    $rdi                  examine: as a string
p/x    $rax                  print in hex
```

The conditional breakpoint deserves emphasis. A breakpoint in a loop that runs ten
thousand times is useless; the same breakpoint with `if i == 9999` is precise. Most
of the skill in using a debugger is stopping at the *right* moment rather than
stopping often.

And when observation should not stop the program at all, script it:

```
break *0x401156
commands
  silent
  printf "acc = %#x\n", $rax
  continue
end
```

That logs a value every time the location is hit, without pausing. For anything more
complex, gdb embeds Python, and a `gdb.Breakpoint` subclass whose `stop()` returns
`False` logs and continues.

Turning a manual observation into an automated trace is one of the highest-leverage
moves available, and it is where a large fraction of real dynamic analysis time goes.

---

## 7. `strace` and `ltrace`

Before attaching a debugger at all, watch the boundaries.

```bash
strace ./program        # every system call
ltrace ./program        # every library call
```

`strace` shows the syscalls: which files are opened, what is read and written,
whether it connects to the network, what environment variables it examines. Thirty
seconds of `strace` frequently answers "what does this thing even touch?" better
than an hour of reading.

`ltrace` shows calls into shared libraries: `strcmp`, `malloc`, `getenv`, and their
arguments. It is less reliable — it depends on the calls actually going through the
dynamic linking mechanism, which Lecture 8 explains, and it will miss anything
inlined or statically linked.

Both are triage instruments. They tell you where to look. They do not tell you what
the program means.

---

## 8. Patching, and what it actually proves

You will discover that flipping one byte makes a licence check pass.

```
je   (0x74)  ↔  jne  (0x75)     invert a branch
any jump     →  nop  (0x90)     delete a branch
function     →  ret  (0xc3)     stub it out entirely
```

In gdb you can do it live; on disk you can do it permanently:

```python
f = open('program', 'r+b')
f.seek(0x1189)          # file offset of the je
f.write(b'\x75')        # make it jne
f.close()
```

This works, it feels like winning, and it is worth being precise about what it is.

**A patch is an experiment.** Flipping a branch tests the hypothesis "this branch is
the check". If the program then behaves as you expected, the hypothesis is supported.
If it crashes three functions later, you have learned that the check has a second
part, and that is also a result.

What a patch is *not* is understanding. Consider the difference between two ways of
defeating a licence check:

**The cheap way.** Break on the comparison, flip the flag, the program prints
"Valid". Elapsed time: two minutes. What you now know: nothing. You cannot produce a
valid key, you do not know what makes a key valid, and if there is a second check
you will walk into it blind.

**The real way.** Break on the comparison and read *both* operands. One is derived
from your input; the other is computed. Where did the computed one come from? Set a
watchpoint on it. It is written after a loop over your input bytes. Characterise the
loop — is it a sum? A shift-and-xor? Feed known inputs and watch the accumulator.
Now you can state what a valid key must satisfy, and construct one.

The second takes longer and gives you the thing you actually wanted. The first
disables a check; the second understands it.

A useful rule: **if your solution only works on this binary, you reverse engineered
the binary. If it works on any input, you reverse engineered the algorithm.**

---

## 9. Where automated help fails here

This lecture's failure mode is different from the previous ones, and more
representative of how you will actually use assistance in practice.

The realistic use of a model in dynamic analysis is not "explain this binary." It is
**"write me the gdb script that logs the accumulator each iteration."** That is a
genuinely good use: it is boilerplate, the syntax is fiddly, and generating it is
faster than writing it.

What comes back is usually about ninety percent right. The structure is correct, the
API calls exist, it looks entirely reasonable. And one detail is wrong:

- it reads `$rax` when the accumulator lives in `$rbx` at that point;
- or it hooks the top of the loop body, sampling the accumulator *before* the round
  updates it, so every logged value is one iteration stale;
- or it uses a `commands` block without `end`, and nothing runs at all.

The third you notice immediately. The first two you do not, because the script runs
and produces a table of plausible numbers, and you proceed to analyse a trace in
which every value is wrong.

The fix takes ten seconds *if you know where the value actually lives*. If you do
not, you re-prompt, and you get another plausible script with a different subtle
error, because the model has the same blind spot each time and no access to the
running program to check against.

This is the shape of the thing to expect: **not "AI cannot reverse engineer" but "AI
writes tooling that is ninety percent right, and the ten percent silently
invalidates the output."** You are not competing with it. You are the part of the
loop that can check it, and that requires knowing which register holds what — which
is Lecture 2.

---

## Summary

- Static analysis: all paths, imprecise values. Dynamic: one path, exact values. Real
  work alternates.
- A process has a private virtual address space. `info proc mappings` is ground truth
  about what is loaded where.
- A syscall is the user/kernel boundary: number in `rax`, `syscall` instruction. It
  cannot be avoided, which makes it an excellent observation point.
- ASLR randomises addresses per run; gdb disables it. Record offsets from a known
  base, not absolute addresses.
- A software breakpoint is an `int3` (`0xCC`) byte patched over the instruction. A
  program can detect this — that is a standard anti-debug technique.
- Hardware watchpoints use CPU debug registers, patch nothing, and answer "who is
  writing to this?". There are four.
- Most debugger skill is stopping at the *right* moment: conditional breakpoints, and
  scripts that log without stopping.
- `strace`/`ltrace` before anything else: they tell you what the program touches.
- **A patch is an experiment, not a victory.** If your solution only works on this
  binary you reversed the binary; if it works on any input you reversed the algorithm.
- Generated tooling is ~90% right, and the wrong 10% is usually a register name or a
  sample point — which silently invalidates every number it prints.

## Reading

- *Practical Binary Analysis*, chapters 8–9 — dynamic analysis and instrumentation.
- Exercise: write a gdb Python script that logs every `malloc` size in some program,
  then compare it against `ltrace -e malloc`. Where they disagree, work out which is
  right and why.
