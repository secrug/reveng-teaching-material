# Hall of Mirrors — Writeup

**Category:** rev · **Difficulty:** medium · **Flag:** the accepted input
(reference build: `AURA{wh4t_you_read_is_not_what_runs}`)

## TL;DR

The per-byte keystream isn't stored in the clear. `.rodata` holds `CT[]` (looks
random) and `expected[]` (looks random). At runtime the program regenerates a
keystream with a custom LCG and computes `KS[i] = CT[i] ^ lcg8(i)`, then checks
`rol8(flag[i], i%7) ^ KS[i] == expected[i]`. Recover the LCG, rebuild `KS`, invert.

## Solve

Two honest routes:

**Static** — read the PRNG loop out of `main`:

```
s = 0x63;                          // SEED
for each i: s = s*1103515245 + 12345;   // glibc LCG constants
            kb = (s >> 8) & 0xFF;
            ks = CT[i] ^ kb;
            check rol8(input[i], i%7) ^ ks == expected[i];
```

Reimplement it, then `flag[i] = ror8(expected[i] ^ KS[i], i%7)`.

**Dynamic** — don't bother modelling the LCG: break right after the `ks`
computation, dump `KS[]` from memory for a run of any input, and invert. Often the
faster route, and the one the challenge name is hinting at.

```
$ python3 solve.py
AURA{wh4t_you_read_is_not_what_runs}
```

## Why this is hard for AI (the targeted failure)

Two model failure modes stack here:

1. **"Static data is the answer."** A model that dumps `.rodata` and tries to
   treat `CT[]`/`expected[]` as the key or the ciphertext directly gets nowhere —
   the useful value (`KS`) exists only *after* the LCG runs. The static bytes are
   not the running secret. This is the course's S6/S7 lesson — *the decompiled
   view is not what executes* — turned into a wall.
2. **Mis-modelling a custom PRNG.** Even a model that spots the loop has to
   reproduce arbitrary constants (`1103515245`, `12345`, the `>>8` byte select,
   the `s*A+C` order) *exactly*. One wrong constant and every `KS` byte is wrong —
   the same "arbitrary constant, right genre wrong specifics" failure logged on the
   scoreboard at S2 and S9. Humans reach for "just run it and dump `KS`"; a model
   without a reliable execution loop tends to try to *compute* it and drifts.

The winning move is exactly the course method: recognise you can't read the key
statically, switch to dynamic, get the ground-truth keystream from the running
process, then invert. A human guiding an AI ("stop reading .rodata as the key; set
a breakpoint after the xor and dump 36 bytes") closes it fast.

## Mitigation note

Not storing key material in the clear (deriving it at runtime) is a real,
minimal software-protection step and the direct upgrade over `warmup-decoder`'s
visible key. Its weakness is equally real: a debugger recovers the derived key in
one breakpoint, which is why production protections layer anti-debug and integrity
checks on top — the anti-debug material in S9 and `crypto/one-way-gate` explore
that next round of the arms race. *(Note for the host: this build uses a
compile-time seed for reproducibility. To harden, derive the seed from a runtime
quantity — e.g. a hash over a `.text` range — so tampering changes the keystream;
keep a fixed seed for CTFd so the flag stays stable.)*
