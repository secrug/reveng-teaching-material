# Lab 5 — Reading data

**Time:** Lab A 40 min + Lab B 30 min · **Pack:** `s05/access`, `s05/layouts`,
`configparse` + `sample.cfg`

---

## Lab A

### Core — Array or struct?

`access` has three functions, each walking a data structure. For each, decide:
array or struct? Element/field sizes? Draw the memory layout.

**Deliverable:** three annotated layout drawings with byte offsets.

#### Solution outline

Fn1: array of `int` (`[rdi+rcx*4]`, variable index). Fn2: struct (constant
offsets `+0`, `+8`, `+16`). Fn3: array of structs (`[rdi + rcx*24 + off]` — a
scaled index *and* a field offset; the `*24` is the struct stride). The tell for
array-vs-struct is variable-index-times-scale (array) vs constant-offset (field).

### Stretch — Reconstruct with padding

Reconstruct the full struct in `access` fn3, **padding included**, and compute
`sizeof`. Verify by dumping an instance in gdb (`x/24xb <ptr>`).

#### Solution outline

The struct has a deliberate alignment hole (e.g. `int; char; int; long`). `sizeof`
is *not* the sum of field sizes. Grade the padding, not just the fields.

### Boss — The ambiguous access (explain-back)

`layouts` shows one access pattern consistent with several structs. Produce the
**candidate set**, and for each candidate, the **single observation** that would
confirm or kill it.

#### Solution outline

Two `[rdi]`,`[rdi+8]` 8-byte reads → could be `{long;long}`, `{long;ptr}`,
`{double;long}`, etc. Disambiguators: is `[rdi+8]` dereferenced? (→ pointer). Is
`[rdi]` loaded with `movsd`? (→ double). Is it passed to `free`? (→ heap pointer).
The right answer is a set + observations, *not* a single confident guess. Praise
"I can't tell yet, but X would tell me."

---

## Lab B — Prove the AURA-7 struct

The `aura_config` struct (recovered live in Teach B) is provided so nobody's
blocked.

- **Core:** write it in C; compute `sizeof` with correct padding.
- **Stretch (flagship):** hand-craft a config file — raw bytes at the right
  offsets — that `auractl` **accepts**. This proves the struct is right.
- If the checksum blocks acceptance: record it as an open question for S9 and move
  on. Do **not** grind on it.

### Solution outline

The forged config must have: magic at +0, version at +4, a valid pointer-or-index
field, etc., matching the recovered layout. Acceptance = proof. The checksum
trailer (the S1 open question) will likely block full acceptance — that's
intended; students should get the *layout* right and hit the checksum wall,
recording it for S9. Provide a `mkconfig.py` skeleton that writes correctly-padded
bytes, minus the checksum, in the solutions repo.

---

## TA notes

Padding is the whole session. Every layout drawing should shade the holes. The
config-forging task is the "prove it, don't assert it" lesson made physical: a
struct that makes the program accept a file is *known*; a struct that merely looks
right is a hypothesis.
