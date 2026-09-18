# Lab 8 — Read the structure / write a hook

**Time:** Lab A 40 min + Lab B 30 min · **Pack:** `s08/stripped_fns`, `preloadme`
+ `evilhook.c` skeleton; the ELF card

---

## Lab A — Read the structure

### Core — Full ELF triage

Run a complete `readelf` triage of a provided binary and report: architecture,
executable vs shared vs relocatable, static vs dynamic, the interpreter, the
`NEEDED` libraries, and the **PLT function list** (what library functions it
calls).

```bash
readelf -h X   # header
readelf -l X   # segments
readelf -d X   # dynamic / NEEDED
readelf -S X   # sections
objdump -d -j .plt X   # or: objdump -R X for the relocations naming PLT entries
```

**Deliverable:** the triage report, ending with: "from the PLT, this program can
_____" (e.g. "open files, use the network, hash something").

### Stretch — Name stripped functions from their calls

`stripped_fns` has no symbols. Recover function boundaries and **re-name** the
internal functions from the PLT calls they make and their xrefs. A function
calling `socket`/`bind`/`listen` is server setup; one calling `fopen`/`fread` is
a file loader.

**Deliverable:** a renamed function map with the evidence (which PLT calls named
each one).

#### Solution outline

The point: dynamic symbols survive stripping (S8 headline), so PLT calls are a map
into stripped code. Grade the *inference* — "it calls `inet_pton` then `connect`,
so it's making an outbound connection."

### Boss — Follow the GOT (explain-back)

Follow one library call through PLT→GOT in gdb: show the GOT slot **before** the
first call (points back into the PLT stub) and **after** (points into libc).
Explain lazy binding from what you saw.

```bash
(gdb) b main
(gdb) x/gx <GOT slot addr>     # before: PLT+6-ish
(gdb) # step past the first call to that function
(gdb) x/gx <GOT slot addr>     # after: a libc address
```

**Deliverable:** the two GOT values + your lazy-binding explanation, to a
neighbour, notes closed.

---

## Lab B — Write your own hook

- **Core:** write an `LD_PRELOAD` shim that logs every call to **one libc
  function `auractl` actually uses** — find one first via `ltrace`/PLT, don't
  guess. Confirm the log fires.
- **Stretch:** make the hook *alter* behaviour (e.g. `getenv("AURA_LICENSE")`
  always returns a chosen string) and confirm the effect on the program.
- **Required note:** write down one thing your hook **cannot** reach and why
  (inlined code, internal calls, direct syscalls, static linking).

```c
// evilhook.c skeleton (full in solutions repo)
#define _GNU_SOURCE
#include <dlfcn.h>
char *getenv(const char *name) {
    char *(*real)(const char*) = dlsym(RTLD_NEXT, "getenv");
    if (!strcmp(name, "AURA_LICENSE")) return "CHOSEN-VALUE";
    return real(name);
}
```
```bash
gcc -shared -fPIC evilhook.c -o evilhook.so -ldl
LD_PRELOAD=./evilhook.so ./auractl ...
```

#### Solution outline

The "cannot reach" note is the graded insight and the setup for the drill: the
licence comparison is **inlined**, so no PLT-crossing call to hook. A student who
tries to hook `strcmp` and finds it never fires has learned the boundary the hard,
correct way.

---

## TA notes

Steer students to `ltrace` *first* to find a real call before writing a hook.
Guessing `strcmp` (the model's move) and watching it do nothing is instructive
exactly once — after that, `ltrace` shows them what actually crosses the boundary.
