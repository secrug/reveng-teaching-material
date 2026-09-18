# Lab 1 — Eight mystery files

**Time:** 40 min · **Pack:** `s01/mystery1`…`mystery8`, plus `probe.c`

---

## Core — Identify all eight (target: everyone)

For each of the eight files, decide what it is and **write down which single piece
of evidence decided it.** "`file` said so" is not an acceptable answer — you must
confirm against the bytes.

Toolbox: `file`, `xxd | head`, `strings -n 8`, `nm -C`, `readelf -h`.

**Deliverable:** a table.

| file | verdict | deciding evidence |
|---|---|---|
| mystery1 | ELF executable, dynamically linked, not stripped | `readelf -h` type EXEC/DYN; `.symtab` present |
| … | | |

### Solution outline (lecturer)

The pack is built (see `binaries/BUILD-PLAN.md` §S1) to contain, in some order:

1. A normal ELF executable, not stripped.
2. The same program, **stripped** (`strip`) — same code, no `.symtab`.
3. An ELF **shared object** (`.so`) — `readelf -h` type `DYN`, no `main`.
4. An ELF **relocatable object** (`.o`) — type `REL`, has relocations.
5. A **PNG** — magic `89 50 4E 47`, `file` nails it, `xxd` confirms `IHDR`.
6. A **gzip** — magic `1f 8b`, high entropy after the header.
7. A **static** ELF executable — large, `readelf -d` shows no `NEEDED`.
8. A **corrupted PNG** — magic byte flipped so `file` says "data"; still a PNG by
   structure (the AI-hostile artifact — see Drill).

Deciding evidence per file is the point; the verdict alone is worth little.

### Watch for

- Students trusting `file` and stopping. Every time: *"and if `file` is wrong?"*
- Confusing the `.so` and the executable — both are ELF `DYN` on modern systems
  (PIE). The tell is `main`/entry behaviour and `readelf -d` SONAME.

---

## Stretch — What the optimiser destroys

Compile `probe.c` three ways and diff the assembly:

```bash
gcc -O0 -S probe.c -o probe_O0.s
gcc -O2 -S probe.c -o probe_O2.s
gcc -Os -S probe.c -o probe_Os.s
```

**Deliverable:** for each step up in optimisation, name three concrete things
that were destroyed or transformed (e.g. "the loop was replaced by a closed-form
multiply", "the local variable no longer touches memory", "the function was
inlined and no longer exists as a symbol").

### Solution outline

`probe.c` contains (by design) a summation loop (→ closed form at `-O2`, the
many-to-one demo), a tiny helper called once (→ inlined away), and a local used
in a loop (→ lives in a register at `-O2`, in memory at `-O0`). Expect students
to notice: memory traffic vanishes, the helper symbol disappears, the loop
structure is gone or unrolled, dead code removed.

---

## Boss — The hidden twin (explain-back)

Two of the eight files are the **same program**, different builds (#1 and #2: one
stripped, one not — or a `-O0` and `-O2` pair, depending on your build). Find the
pair and **prove** they're the same program, not just similar.

**Deliverable:** the pair, plus your proof. Explain it to a neighbour, notes
closed.

### Solution outline

Proof paths that count: identical `.rodata` strings; identical structure under
`objdump -d` modulo symbol names; same entry behaviour; a distinctive constant or
string appearing in both. A student who says "they're both ELF" has not proven
anything — push for a *distinguishing* feature shared by exactly these two.

---

## Notes for the TA

The single habit this lab exists to install: **`file` is a hypothesis, `xxd` is
evidence.** Every intervention should reinforce it. A student who leaves reaching
for `xxd` to confirm a guess has gotten the whole session's value even if they
only finished Core.
