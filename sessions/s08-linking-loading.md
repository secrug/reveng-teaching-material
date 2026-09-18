# Session 8 — Formats, linking and loading

**The one idea:** an executable isn't a monolith — it's a structured document the
loader assembles into a process. Once you know the structure, you can read it,
navigate it, and intervene in it without ever touching the code.

---

## Outcomes

1. Read an ELF's header, segments (program headers) and sections; say what the
   loader uses vs what the linker used.
2. Explain static vs dynamic linking and what relocations do.
3. Trace a library call through the PLT and GOT and explain lazy binding.
4. State exactly what stripping removes and — crucially — what it doesn't.
5. Use `LD_PRELOAD` to interpose a function without modifying the binary, and say
   what it *can't* reach.
6. Separate "the concept" from "this ISA's spelling" via a PE/ARM64 contrast.

---

## Prep checklist

- [ ] `s08/` pack: `hello_dyn`, `hello_static`, `stripped_fns`, `preloadme` +
      `evilhook.c`, and small PE + ARM64 sample binaries for the contrast
- [ ] Reference card **#? (ELF map)** — the ELF layout diagram, printed
- [ ] `readelf`, `objdump`, `patchelf`(opt), a PE tool (`objdump -x` handles PE)
- [ ] Casts: `s08-demo1.cast` (PLT/GOT walk), `s08-demo2.cast` (LD_PRELOAD)

---

## 0:00 — Warm-up (15 min)

1. How does a software breakpoint work, in one sentence?
2. What's the difference between a syscall and a library call?
3. `strace` shows `connect()`. What did the program just do, and did you need to
   read any asm to know?
4. Patch vs understand — when is a patch the *wrong* answer?
5. AURA-7: what did we learn the licence transform looks like? *(shift-xor-accumulate)*

---

## 0:15 — Cold open (10 min)

Two files on screen:

```
$ ls -l hello_dyn hello_static
-rwxr-xr-x  16696   hello_dyn
-rwxr-xr-x 871280   hello_static
```

Same source. Same output. **Question:** why is one 50× bigger? And which one will
still run in ten years on a machine with different libraries?

Written prediction. Gets at the whole static/dynamic tradeoff before it's taught.
Resolved at 2:55.

---

## 0:25 — Teach A: the anatomy of an executable (35 min)

### A1 — ELF, two views (12 min)

The key insight, on the board: an ELF is described **twice**, for two readers.

```
        ┌─────────────────────┐
        │    ELF header       │  "I am x86-64, entry point 0x1050"
        ├─────────────────────┤
        │  program headers    │  ◀── THE LOADER reads these (segments)
        │  (segments: what to │      "map these bytes here, R-X; those, RW-"
        │   map into memory)  │
        ├─────────────────────┤
        │   ...code & data... │
        ├─────────────────────┤
        │  section headers    │  ◀── THE LINKER read these (.text .data ...)
        │  (sections: .text,  │      "here's where each named piece lives"
        │   .rodata, .symtab) │      (can be stripped; loader doesn't need them)
        └─────────────────────┘
```

> "Segments are for *running* — the loader maps them. Sections are for *linking
> and tooling* — the linker used them, and Ghidra uses them, but the running
> program doesn't need them. That's why you can strip section info: the program
> still runs, it's just harder for *you* to read. Stripping attacks the analyst,
> not the machine."

Live tour, `readelf`:

```bash
readelf -h hello_dyn      # header: class, entry, type
readelf -l hello_dyn      # program headers (segments) — LOAD, INTERP, DYNAMIC
readelf -S hello_dyn      # sections — .text .rodata .plt .got .symtab ...
readelf -d hello_dyn      # dynamic: NEEDED libc, symbol tables
```

The sections that matter for RE, off the ELF card:
`.text` (code) · `.rodata` (constants) · `.data`/`.bss` (globals, S5) ·
`.plt`/`.got` (the dynamic-call machinery, next) · `.symtab`/`.dynsym`
(names) · `.rela.*` (relocations).

### A2 — Linking: static vs dynamic, and relocations (11 min)

> "Your code calls `printf`. But `printf` lives in libc, whose address the linker
> didn't know and *couldn't* know — it's decided at load time. So the linker
> leaves a blank and a note: 'fill in `printf`'s real address here once you know
> it.' That note is a **relocation.**"

- **Static** (`hello_static`): libc is copied *into* the binary. Big, standalone,
  runs forever. Nothing to resolve at load — the cold-open size difference.
- **Dynamic** (`hello_dyn`): libc is referenced, loaded separately, addresses
  patched in at runtime. Small, shared, dependent on what's installed.

`readelf -r hello_dyn` — show the relocation entries: symbol name, where the
address goes.

### A3 — PLT and GOT: the indirection everyone finds confusing (12 min)

Take it slow; draw it live and step it in gdb.

```
  call printf@plt
        │
        ▼
  ┌── .plt ──┐        ┌── .got.plt ──┐
  │ printf:  │──jmp──▶│ [printf slot]│──▶ (1st call) resolver → finds real printf
  │  jmp     │        │              │              writes real addr back here
  │ [GOT slot]        │              │──▶ (later)    jumps straight to real printf
  └──────────┘        └──────────────┘
```

> "Calls to library functions don't go straight to libc. They go to a stub in the
> **PLT**, which jumps through a slot in the **GOT** — a table of addresses filled
> in at runtime. The first call runs the resolver (slow, once); it writes the real
> address into the GOT; every later call is a fast indirect jump. That's **lazy
> binding** — nothing is resolved until first use."

Prove it live in gdb:

```bash
gdb hello_dyn
(gdb) b main
(gdb) x/gx <printf GOT slot>       # before first call: points back into PLT
(gdb) # step past the first printf
(gdb) x/gx <printf GOT slot>       # after: points into libc — it changed
```

> "Why do you care? Three reasons. One: in a stripped binary, the PLT still has
> *named* library calls — `strcmp`, `memcpy`, `socket` — because dynamic symbols
> can't be stripped, they're needed to link. That's a map into stripped code, and
> it's why stripping isn't the end of the world. Two: the GOT is a table of
> function pointers you can *watch* or *overwrite*. Three: it's the mechanism
> behind the trick I'm about to show you."

**What stripping removes vs keeps** — the S8 headline, onto the card:

| Stripped away (`.symtab`) | Always survives |
|---|---|
| your function names | dynamic symbols (`.dynsym`) — library calls |
| local variable names | PLT/GOT structure |
| debug info | strings, control flow, the code itself |

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: read the structure (40 min)

Full spec: [`labs/s08-lab.md`](../labs/s08-lab.md).

- **Core** — full `readelf` triage of a binary: type, linkage, interpreter,
  NEEDED libraries, and the PLT function list. What does it call?
- **Stretch** — `stripped_fns`: recover function boundaries and *re-name* internal
  functions using PLT calls and xrefs (a stripped function that calls `socket`,
  `bind`, `listen` is a server setup — name it). Bridges S6 method to S8 data.
- **Boss** — follow one library call through PLT→GOT in gdb, showing the GOT slot
  before and after resolution. Explain lazy binding from what you observed.
  (Explain-back.)

---

## 1:50 — Teach B: live demo — LD_PRELOAD, the no-touch intervention (25 min)

**Target:** AURA-7's `auractl` licence check — defeated *without modifying the
binary at all*.

The concept:

> "`LD_PRELOAD` tells the loader: load *my* library first, and if I define a
> function with the same name as one in libc, mine wins. Every call the program
> makes to that function comes to me instead. I can intercept `strcmp`, log it,
> lie about the result — and I never touched the target binary."

Build it live — `evilhook.c`:

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <stdio.h>

int strcmp(const char *a, const char *b) {
    // real one, in case we want to fall through
    int (*real)(const char*,const char*) = dlsym(RTLD_NEXT, "strcmp");
    fprintf(stderr, "[hook] strcmp('%s', '%s')\n", a, b);
    return 0;   // <-- everything is equal now
}
```

```bash
gcc -shared -fPIC evilhook.c -o evilhook.so -ldl
LD_PRELOAD=./evilhook.so ./auractl activate --key WHATEVER
```

**Scripted wrong turn — and it's the AI-hostile point of the session:** run it,
expect the check to fall. It *doesn't* fall.

> "Huh. My hook logged nothing and the check still failed. So `auractl` isn't
> using libc's `strcmp` here. Why not?"

Investigate: the comparison is **inlined** (S6!) — the compiler emitted the byte
loop directly, no `call strcmp` for `LD_PRELOAD` to catch. Pivot to a function
that *is* an external call (the key derivation calls `memcpy`, or the config read
calls `fopen`), hook that instead, and show it working.

> "That's the real lesson. `LD_PRELOAD` is powerful and it has a hard boundary:
> it only catches calls that actually go through the PLT to a shared library.
> Inlined code, internal functions, direct syscalls — invisible to it. The
> `strcmp` that isn't there is exactly the kind of thing a model will tell you to
> hook, confidently, because hooking `strcmp` is the textbook example."

`RTLD_NEXT` explained in one line: "how the hook calls the *real* function when
it wants to — 'the next `strcmp` after me in the search order.'"

### The 10-minute contrast: same concept, different spelling

Deliberately brief. The goal is transfer, not coverage.

- **PE (Windows):** show `objdump -x` of a small PE. The **Import Address Table**
  is the GOT's cousin — same idea (a table of resolved addresses), different name
  and layout. "DLL instead of .so, IAT instead of GOT, `LoadLibrary` instead of
  the ELF loader. The *concept* is identical."
- **ARM64:** show the same tiny function compiled for ARM64. Fixed 4-byte
  instructions, different registers (`x0`–`x30`), args in `x0`–`x7`, return in
  `x0`. "Everything you learned about *the machine as a state machine, calling
  conventions, the stack* is true here. Only the spelling changed. If you thought
  you were learning 'x86', you were actually learning 'how machines work' — and
  that transfers."

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: write your own hook (30 min)

- **Core:** write an `LD_PRELOAD` shim that logs every call to one libc function
  `auractl` actually uses (find one via `ltrace`/PLT first — don't guess).
- **Stretch:** make the hook alter behaviour (e.g. make `getenv("AURA_LICENSE")`
  always return a chosen value) and confirm the effect.
- **Explicit required note:** each student writes down one thing their hook
  *cannot* reach and why.

Seed the drill: **"ask a model how to bypass AURA-7's licence check with
LD_PRELOAD. Keep its answer."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** Model output, near-universal: *"Just `LD_PRELOAD` a `strcmp` that
returns 0 and the licence check passes."*

1. *State it.* Hook `strcmp`, return 0, done.
2. *What would falsify it?* — if the check uses `strcmp`, there's a `call
   strcmp@plt` in the disassembly and the PLT lists `strcmp`. Check both.
3. *Observe.* `objdump -d | grep strcmp` — nothing. Not in the PLT. The
   comparison is inlined. The hook would run and change nothing.
4. *Verdict.* **Wrong — hooks a call that doesn't exist.** Reason: the model gave
   the *textbook* `LD_PRELOAD` answer (hook `strcmp`) without checking whether
   this binary actually calls `strcmp`. It answered the generic question, not the
   specific binary. Interposition only works on calls that cross the PLT boundary
   — the one fact the generic answer omits. Record it.

**Cold-open reveal.** `hello_static` is 50× bigger because libc is baked in; it'll
run in ten years regardless of the system libraries. `hello_dyn` is small and
shares libc but depends on what's installed. That dependency is exactly the seam
`LD_PRELOAD` pries open — dynamic linking is a flexibility *and* an attack
surface.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 8 | `LD_PRELOAD` a `strcmp` returning 0 bypasses the licence check | ✗ Wrong (no such call) | Textbook answer; this binary inlines the comparison, no `call strcmp@plt` exists. Interposition only catches PLT-crossing calls — the fact the generic answer omits |

---

## Lecturer notes

**PLT/GOT is the confusing bit — go slow and step it live.** The GOT-slot-changes
-after-first-call demo is what makes lazy binding concrete. Don't just describe
it; show the address change in `x/gx`.

**Don't oversell the contrast segment.** Ten minutes, transfer only. The failure
mode is turning it into a mini ARM64 lecture and blowing the clock. One function,
one point: same concept, different spelling.

**The inlined-strcmp wrong turn must land.** It's the session's whole AI lesson.
If your build has an actual `call strcmp`, the demo and drill both collapse —
**verify the comparison is inlined in your `auractl` build** (`BUILD-PLAN.md` §S8
specifies `-O2` + a byte loop precisely to guarantee this).

**Running long.** Cut Lab A Boss (the demo covers PLT/GOT live), then trim the PE
half of the contrast (keep ARM64 — the "you learned how machines work, not x86"
point is worth more). Protect the LD_PRELOAD demo including its wrong turn.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-8)

- **Read:** CS:APP ch. 7 (linking), 30 min — the definitive treatment.
- **Do:** build a program static and dynamic; compare sizes and `readelf -d`;
  break it by moving a library.
- **Crackme:** crackmes.one difficulty 3 involving dynamic libraries, or a
  "solve with LD_PRELOAD" challenge.
- **Self-check:** 5 questions, answers included.
