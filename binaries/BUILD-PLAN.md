# Binary Build Plan

Every binary the course needs, its source sketch, its compile flags, and — for
each — **the AI-hostile property engineered into it and the failure it is designed
to provoke.** The Falsification Drill only works if the artifacts reliably break
the model in the predicted way, so those properties are specified, not left to
chance.

## Conventions

- Toolchain pinned in the Docker image (`infra/SETUP.md`): a fixed gcc/clang
  version so optimiser output is reproducible across offerings. **If you bump the
  toolchain, re-verify every "AI-hostile property" below** — optimiser changes can
  erase a planted trap.
- `-O0` unless noted; `-O2` where the lesson needs realistic codegen; `-g`
  stripped from anything meant to be read cold; `strip` where "stripped" is
  stated.
- A `Makefile` per session directory builds everything and runs a **verification
  script** (`verify.sh`) that asserts each hostile property still holds (e.g.
  `objdump -d auractl | grep -q 'call.*strcmp' && echo FAIL`). Run it after any
  toolchain change. This is what turns "I hope the drill fires" into "the build
  refuses to ship if it won't."

## The AURA-7 family (built once, reused and extended across sessions)

`auractl`, `aurad`, `aura-fw.bin` — a synthetic embedded telemetry device. Source
lives in `binaries/aura/`. Design constraints:

- **`auractl`** — CLI. Sub-commands dispatched via a **jump table** (S3). Parses a
  binary **config struct with deliberate alignment padding** (S5). Licence check
  is a **custom rolling hash** (shift-xor-accumulate), **compiled `-O2` so the
  comparison is inlined** — no `call strcmp`/`call memcmp` for the licence path
  (S6, S7, S8 all depend on this). Contains a **decoy `check_license()`** that
  returns a constant and whose result is never used (S6).
- **`aurad`** — daemon on a unix socket, speaks `[u8 type][u16 len][payload]`, a
  **state machine** (S9).
- **`aura-fw.bin`** — flat blob: `"AURA"` magic, 2×u16 version, a length field
  that **excludes a trailing checksum** (the S1 open question, closed S9).
- **`enigma`** (S10) — a variant with a *different* recurrence constant and a
  fresh decoy, so prior knowledge doesn't transfer.

**The three load-bearing properties — verify these every offering:**
1. Licence comparison is **inlined** (no PLT call). *(S6/S7/S8/S9/S10)*
2. `check_license` is a **decoy** with an unused return. *(S6/S9/S10)*
3. Config struct has a **padding hole** invisible in the C source. *(S5)*

---

## Session 1 — formats & lossiness

| Binary | Build | Purpose |
|---|---|---|
| `mystery1` | normal ELF, not stripped | baseline |
| `mystery2` | `= mystery1` then `strip` | "same code, no symbols" |
| `mystery3` | `.so`, `-shared -fPIC` | shared object |
| `mystery4` | `.o`, `-c` | relocatable |
| `mystery5` | a real PNG | non-ELF format |
| `mystery6` | a real gzip | high-entropy format |
| `mystery7` | `-static` | static ELF, big |
| `mystery8` | PNG with **1 magic byte flipped** | **AI-hostile** |
| `crackme01` | plaintext password in `.rodata` | strings solves it |
| `crackme01x` | password **XOR'd at startup** | strings fails |
| `probe.c` | source only | the `-O0/-O2/-Os` diff |

**AI-hostile (`mystery8`):** `file` reports "data" because the magic is broken,
but the file is structurally a PNG. Ask a model "what is this file?" from `file`
output → it trusts `file` and says "unknown/data." The `xxd` structure
(width/height in the IHDR, the `IDAT`/`IEND` chunks) says PNG. **Provokes:**
over-trusting a tool's summary instead of the bytes.

**`f`/`g` many-to-one demo:** verify on your pinned compiler that the two source
forms converge at `-O2`. If not, the fallback pair (in `aura/manytoone.c`) uses a
`popcount` written two ways that reliably converge to `POPCNT` or the same shift
sequence.

## Session 2 — machine semantics

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `trace1` | `-O0`, asm-authored 20 instrs | hand-trace; contains a 32-bit-write zero-extension |
| `trace2` | `-O0`, uses memory + `lea` | hand-trace with memory |
| `trace3` | `-O0`, asm-authored | **AI-hostile:** the final register state depends on a 32-bit zero-extension. **Provokes:** model tracks arithmetic correctly, reports full 64-bit value, misses the upper-half zeroing. |
| `sizes` | `-O0` | the live operand-size demo |
| `lea_vs_mov` | `-O0` | the live `lea`/`mov` demo |
| `decode.txt` | raw bytes | hand-decode drill |

## Session 3 — control flow

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `shapes` | 6 fns, `-O0` then `-O1` | the six-shapes demo & matching game |
| `dispatch` | `switch`, `-O2` | jump table demo |
| `recon1` | if/else, `-O0` | inverted-jump lesson |
| `recon2` | counted for, `-O0` | loop shape |
| `recon3` | nested loop + break, **bound is `<=`** | **AI-hostile:** `jle` where the common idiom is `jl`. **Provokes:** model reconstructs `i < n` (off-by-one); caught by counting breakpoint hits. |
| `recon4` | do/while + `cmov`, `-O2` | branchless decision |

## Session 4 — stack & ABI

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `frames` | `-O0` | prologue/epilogue, locals |
| `fact` | recursive, `-O0` | the live recursion/stack demo |
| `redzone` | leaf fn, `-O2` | red-zone demo |
| `retaddr` | **`-fno-stack-protector -z execstack`**, `-O0` | the return-address demo. **Build note:** must have no canary or the overwrite demo needs extra steps. Document that this is deliberately unhardened *for teaching* and is not representative. |
| `sigs` | 6 fns, stripped, arities 0–3 | signature recovery. **AI-hostile:** one fn uses a **non-standard calling convention** (asm-authored, args in `r10`/`r11` or on the stack). **Provokes:** model assumes SysV, reads args from `rdi`/`rsi`, gives a confident wrong signature. |

## Session 5 — data & types

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `access` | 3 fns, `-O0` | array vs struct vs array-of-struct |
| `layouts` | `-O0` | the ambiguous-access demo (candidate set) |
| `storage` | globals in .data/.bss/.rodata | storage-class demo |
| `heaplife` | malloc/free, `-O0` | heap-pointer shape |
| `configparse` | part of `auractl`, `-O2` | **AI-hostile:** the config struct has a **3-byte alignment hole** after a `char`/`u8` field. **Provokes:** model sums field sizes and places the next field 3 bytes too early; real offset is padded. Verify the hole survives your compiler. |
| `sample.cfg` | data | the file to match |

## Session 6 — tools & decompilers

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `overlap` | jump table in `.text`, `-O2` | linear-sweep desync demo |
| `auractl` (fresh copy) | `-O2`, stripped-ish | Ghidra target. **AI-hostile ×2:** (1) a **signedness misread** — an unsigned comparison the decompiler renders as signed (or vice-versa), changing meaning; (2) the **`check_license` decoy**. **Provokes:** decompiler wrong on (1) verifiable in gdb; both decompiler and LLM narrate the decoy (2), caught by xref showing the return is unused. |

**Verification is critical here.** `verify.sh` must confirm both the decoy exists
(function present, return value unused at its single call site) and the signedness
quirk survives. If a compiler update "fixes" the decompiler's rendering, re-plant
the signedness trap (a `size_t`/`int` mix reliably does it).

## Session 7 — dynamic

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `licensed` | reversible transform check, `-O0` | break/observe/keygen |
| `phone_home` | opens a file + a (local, harmless) socket | strace/ltrace demo |
| `patchme` | simple `je` check, `-O0` | patching demo |
| (AURA-7 `auractl`) | reused | the two-ways-to-win demo |

**Hostile artifact this session is the *tooling*, not a binary:** the model-written
gdb script. No special build needed — the drill is that the model produces a
subtly wrong script (wrong sample point / register). Provide the *correct*
`logtransform.py` in solutions so the TA can show the diff.

## Session 8 — linking & loading

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `hello_dyn` | dynamic, `-O0` | the 16 KB half of the cold open |
| `hello_static` | `-static` | the 871 KB half |
| `stripped_fns` | network+file fns, stripped | name-from-PLT lab |
| `preloadme` | calls a hookable libc fn | LD_PRELOAD lab |
| `evilhook.c` | source skeleton | the hook |
| a small **PE** | cross-compiled (mingw) or prebuilt | IAT contrast |
| a small **ARM64** ELF | cross-compiled (aarch64-gcc) | ISA contrast |
| (AURA-7 `auractl`) | reused | **AI-hostile:** licence comparison **inlined**, so no `call strcmp@plt`. **Provokes:** model says "LD_PRELOAD strcmp→0"; the hook never fires because the call doesn't exist. `verify.sh` asserts no `strcmp`/`memcmp` PLT entry on the licence path. |

## Session 9 — methodology

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `shapes_zoo` | 8 algo fns, `-O1` | constant/shape recognition (base64, CRC32, XOR, Caesar, state machine, FNV-ish, memcpy, parser) |
| `antidebug_demo` | `ptrace(TRACEME)` self-attach, `-O0` | anti-debug recognise-and-defeat |
| `packed_demo` | any binary run through `upx` | packer recognition |
| (full AURA-7) | reused | the 45-min crown-jewel reverse. **AI-hostile:** the licence recurrence is a **custom rolling hash with a specific rotation/constant**. **Provokes:** model identifies it as CRC32 or a rolling hash with the *wrong* constant — right genre, wrong specifics — diverging from the true accumulator at byte 2. |

## Session 10 — capstone

| Binary | Build | Purpose / hostile property |
|---|---|---|
| `enigma` | fresh AURA-7 variant, `-O2`, stripped | the race target. **AI-hostile:** a **new recurrence constant** (so S9 knowledge doesn't transfer) **plus a planted decoy** function. **Provokes:** AI-only path mis-identifies the algorithm and/or narrates the decoy and cannot recover without independent reasoning. |

**Difficulty tuning (if AI-only no longer stalls):** layer the traps —
(a) put the real recurrence behind a small custom bytecode VM (the S9 "custom VM"
category), so the model must recover opcode semantics before the algorithm;
(b) add a second decoy that is *almost* right (correct genre, wrong constant), so
a model that pattern-matches lands on it confidently;
(c) inline everything and strip aggressively. Re-verify against a current model
before the session; if it still finishes, run the honest "the wall moved" debrief
(see `labs/s10-lab.md`).

---

## The verification discipline (why this file exists)

A course whose AI-hostile artifacts have quietly stopped being hostile — because a
compiler update inlined differently, or a newer model learned the pattern — is a
course whose central demonstration silently fails. So:

1. `make verify` in each session dir asserts every property above.
2. **Before each offering**, run every Falsification Drill against a *current*
   model yourself and confirm it fails as predicted. Update the expected-failure
   notes and the scoreboard exemplars if the failure mode has shifted.
3. If a drill no longer fires, that is a finding, not an embarrassment — the
   honest move is to show students the shifted boundary, per the S10 contingency.
   The method for finding the boundary is the invariant; the boundary's location
   is not.
