# Lecture 8 — Formats, linking and loading

---

## 1. An executable is a structured document

You have been treating binaries as a stream of code. They are not. An executable is
a structured file with a header, a table of contents, and several distinct regions,
assembled into a running process by a program called the loader. Understanding that
structure lets you read a binary, navigate it, and intervene in it — sometimes
without touching a single instruction.

On Linux the format is ELF, the Executable and Linkable Format. The same format
serves three roles: executables you run, shared libraries you link against, and
relocatable object files the compiler emits. `readelf -h` will tell you which.

---

## 2. ELF is described twice

The central insight, because it explains almost everything else: an ELF file
contains **two** tables of contents, aimed at two different readers.

```
        ┌─────────────────────┐
        │    ELF header       │  "x86-64, entry point 0x1050, ..."
        ├─────────────────────┤
        │  program headers    │  ◀── THE LOADER reads these
        │  (segments)         │      "map these bytes here, read+execute;
        │                     │       those bytes there, read+write"
        ├─────────────────────┤
        │   code and data     │
        ├─────────────────────┤
        │  section headers    │  ◀── THE LINKER and your TOOLS read these
        │  (.text .data ...)  │      "here is each named piece"
        └─────────────────────┘
```

**Segments**, described by the program headers, are for *running*. The loader reads
them and maps ranges of the file into memory with permissions: the code segment
read-and-execute, the data segment read-and-write. The loader does not care about
names; it cares about "what goes where, with what permissions".

**Sections**, described by the section headers, are for *linking and tooling*. The
linker used them to combine object files, and Ghidra uses them to label regions, but
the running program does not need them.

The consequence is the headline of this lecture: **you can remove the section
information and the program still runs.** Stripping deletes the section-level symbol
table. The loader never needed it. Stripping is an attack on the analyst, not on the
machine.

---

## 3. The sections that matter

```bash
readelf -h binary      # header: class, type, entry point
readelf -l binary      # program headers — the segments (LOAD, INTERP, DYNAMIC)
readelf -S binary      # section headers — the named pieces
readelf -d binary      # dynamic section — needed libraries, symbol tables
```

The sections you will refer to constantly:

| Section | Contents |
|---|---|
| `.text` | code |
| `.rodata` | constants, string literals (Lecture 1's `strings` goldmine) |
| `.data` | initialised globals |
| `.bss` | zero-initialised globals — occupies no file space |
| `.plt` / `.got` | the machinery for calling shared-library functions — §5 |
| `.symtab` | the full symbol table — **removed by stripping** |
| `.dynsym` | the dynamic symbol table — **survives stripping**, because it must |
| `.rela.*` | relocations — §4 |

That last distinction is the one to hold onto and we return to it in §6.

---

## 4. Linking and relocation

Your program calls `printf`. The compiler, producing your object file, does not know
where `printf` is — it is in libc, which is a separate file, loaded at an address not
decided until the program runs. So the compiler leaves a blank where the address
should go and attaches a note: *"fill in the address of `printf` here once you know
it."*

That note is a **relocation**. `readelf -r` lists them: each names a symbol and the
location that needs patching.

There are two ways to resolve these.

**Static linking** copies the library's code directly into your executable at build
time. Everything is resolved before the program ever runs. The result is large and
self-contained: `hello_static` is 800 KB because it contains a copy of the parts of
libc it uses. It depends on nothing, and it will run unchanged in ten years on a
system with completely different libraries.

**Dynamic linking** leaves the library external. The executable records "I need
libc" (`readelf -d` shows this as `NEEDED`), and at load time the dynamic loader
maps libc into the process and resolves the references. The result is small:
`hello_dyn` is 16 KB because the library lives elsewhere and is shared between every
process that uses it. The cost is a dependency: the program needs a compatible libc
present to run at all.

That size difference — 16 KB against 800 KB for the same source — is entirely the
presence or absence of libc inside the file.

---

## 5. The PLT and the GOT

Dynamic linking raises a question: how does a `call` reach a function whose address
is not known until runtime? The answer is one level of indirection, and it is worth
slowing down for because everyone finds it confusing the first time.

```
  call printf@plt
        │
        ▼
  ┌── .plt ──┐         ┌──── .got.plt ────┐
  │ printf:  │──jmp──▶ │  [printf's slot] │──▶  first call:  resolver runs,
  │  jmp     │         │                  │                  finds real printf,
  │ [GOT slot]         │                  │                  writes address here
  └──────────┘         │                  │──▶  later calls: jump straight there
                       └──────────────────┘
```

Your code does not call `printf` directly. It calls a small stub in the **Procedure
Linkage Table** (`printf@plt`). That stub jumps through a slot in the **Global Offset
Table** — a table of function addresses that is filled in at runtime.

On the *first* call, the GOT slot still points back into the PLT stub, which invokes
the dynamic loader's resolver. The resolver finds the real `printf`, writes its
address into the GOT slot, and jumps there. On every *later* call, the GOT slot
already holds the real address, so the stub jumps straight to it. This is **lazy
binding**: nothing is resolved until first use, so a program that never calls a
function never pays to resolve it.

You can watch it happen:

```
(gdb) x/gx <printf GOT slot>     # before the first call: points into the PLT
(gdb) # ... step past the first printf ...
(gdb) x/gx <printf GOT slot>     # after: a libc address — the slot changed
```

Three reasons to care:

- **In a stripped binary, the PLT entries are still named.** `strcmp`, `memcpy`,
  `socket`, `connect` — these appear because dynamic symbols cannot be stripped. They
  are a map into otherwise anonymous code.
- **The GOT is a table of function pointers you can watch or overwrite.** Both a
  debugging technique and, in other contexts, an attack surface.
- **It is the mechanism behind the interposition trick in §7.**

---

## 6. What stripping does and does not remove

| Removed by `strip` | Always survives |
|---|---|
| your function names (`.symtab`) | dynamic symbols (`.dynsym`) — the library calls |
| local variable names | the PLT/GOT structure |
| debug information | strings, control flow, the code itself |

This is why a stripped binary is inconvenient rather than opaque. You lose the names
the programmer chose. You keep every library call the program makes, every string it
carries, and all of its logic. A function with no name that calls `socket`, `bind`,
`listen` and `accept` is a server's setup code, and you can name it yourself from its
imports — which is exactly the Lecture 6 renaming workflow, now grounded in why the
imports are still there.

---

## 7. Interposition: changing behaviour without touching the binary

`LD_PRELOAD` tells the dynamic loader: load *my* library first, and if I define a
function with the same name as one in a library, use mine. Because dynamically-linked
calls resolve through the GOT at runtime, every such call the program makes arrives
at your function instead.

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>

int strcmp(const char *a, const char *b) {
    int (*real)(const char*, const char*) = dlsym(RTLD_NEXT, "strcmp");
    // ... observe or alter, then fall through if you like ...
    return real(a, b);
}
```

```bash
gcc -shared -fPIC hook.c -o hook.so -ldl
LD_PRELOAD=./hook.so ./target
```

`RTLD_NEXT` means "the next `strcmp` after me in the search order" — how your hook
calls the real function when it wants to. You can log every call, alter arguments,
or lie about return values, and the target binary is never modified.

This is genuinely powerful, and it has a hard boundary, which is the point of the
lecture's failure mode. **`LD_PRELOAD` only catches calls that actually go through the
PLT to a shared library.** It cannot touch:

- **inlined code** — if the compiler emitted the comparison directly instead of
  calling `strcmp`, there is no call to intercept;
- **internal functions** — a call from one of the program's own functions to another
  does not go through the PLT;
- **static linking** — there is no dynamic call to interpose on;
- **direct syscalls** — a program that invokes `syscall` itself bypasses libc
  entirely.

The boundary follows directly from §5: interposition works on exactly the calls that
lazy binding resolves, and nothing else.

---

## 8. The same ideas in other clothes

This is a ten-minute detour with one purpose: to separate the *concept* from *this
ISA's particular spelling*, so that you do not mistake "I learned x86 and ELF" for
"I learned how machines work."

**Windows PE.** A PE executable has the same essential structure under different
names. The equivalent of the GOT is the **Import Address Table**; instead of a `.so`
you link a `.dll`; instead of the ELF loader resolving `NEEDED` libraries, the
Windows loader walks the import table and calls `LoadLibrary`. Run `objdump -x` on a
PE and you will recognise everything — a header, sections, an import table, a list of
needed libraries. The names differ. The idea is identical.

**ARM64.** The same tiny function compiled for AArch64 is unrecognisable at first and
completely familiar underneath. Instructions are all exactly four bytes rather than
one to fifteen. There are more registers — `x0` through `x30` — and arguments go in
`x0`–`x7`, with the return in `x0`. But it is still a state machine executing
instructions, still a stack, still a calling convention, still functions that
announce their arguments through it. Everything from Lectures 2, 3 and 4 is true
here; only the notation changed.

The lesson to carry: if you thought you were learning x86, you were actually learning
how machines work, and that transfers. Each new architecture is new spelling on
grammar you already know.

---

## 9. Where automated help oversells

The failure mode this lecture provokes is the tool giving the *textbook* answer to a
question about a *specific* binary.

Ask a model how to bypass AURA-7's licence check with `LD_PRELOAD` and it will answer,
confidently: preload a `strcmp` that returns 0. This is the canonical `LD_PRELOAD`
example, it appears in every tutorial, and it is exactly what you would do — if the
binary called `strcmp`.

It does not. The comparison is inlined (this is a `-O2` build, and Lecture 6 already
showed the licence logic inlined into its caller). There is no `call strcmp@plt` in
the disassembly, `strcmp` is not in the PLT, and the hook would load, run, and change
nothing.

The check is mechanical and takes one command:

```bash
objdump -d auractl | grep strcmp        # nothing
readelf -r auractl | grep strcmp        # not in the PLT
```

If the function you intend to hook does not appear as a PLT-crossing call, `LD_PRELOAD`
cannot reach it. The generic answer omits the one fact that determines whether it
applies — whether *this* binary makes *that* call across the dynamic boundary — because
the generic answer was produced without looking at this binary's PLT.

The pattern is the Lecture 4 pattern in new clothing: a recognisable question
triggered a recognisable answer, and the recognition happened instead of the
checking. The check is thirty seconds of `objdump`.

---

## Summary

- An executable is a structured document assembled into a process by the loader.
- ELF is described twice: **segments** (program headers) for the loader, **sections**
  (section headers) for the linker and tools. The running program needs only the
  segments — which is why stripping does not stop it running.
- A relocation is a note to fill in an address later. Static linking resolves at build
  time (large, self-contained); dynamic linking resolves at load time (small, shared,
  dependent).
- The PLT/GOT is one level of indirection enabling **lazy binding**: library calls
  resolve on first use. The GOT slot visibly changes after the first call.
- Stripping removes your names (`.symtab`) but never the dynamic symbols (`.dynsym`),
  the PLT/GOT, the strings, or the logic. Library calls map into stripped code.
- `LD_PRELOAD` interposes on dynamically-linked calls and cannot reach inlined code,
  internal calls, static linking, or direct syscalls.
- PE and ARM64 are the same concepts differently spelled. You learned how machines
  work, not x86 specifically.
- The tool's failure here is the textbook answer to a specific question: "preload
  `strcmp`" for a binary that never calls `strcmp`. Check the PLT — thirty seconds.

## Reading

- *Computer Systems: A Programmer's Perspective*, chapter 7 — linking, the definitive
  treatment.
- Exercise: build one program statically and dynamically; compare the sizes and
  `readelf -d`; then break the dynamic one by moving its library and watch the loader
  fail.
