# Wire Format — Writeup

**Category:** rev · **Difficulty:** easy · **Flag:** the accepted input
(reference build: `AURA{p4dding_is_where_the_model_slips}`)

## TL;DR

Each flag byte is transformed by a per-position "step" read from an array of
`struct step { uint8_t op; uint32_t k; }`. The compiler pads that struct to
**8 bytes** (3 padding bytes after `op` so `k` lands on a 4-byte boundary). Read
the array with the real **stride 8** and you recover the ops; assume a packed
5-byte layout and you read garbage. Then invert the op per byte.

## Solve

`main` loops: `step_apply(input[i], STEPS[i % NS])` vs `expected[i]`, where
`step_apply` switches on `op` (0=xor, 1=add, 2=sub, 3=rol) with constant
`k & 0xFF`. All four ops are invertible.

The only subtlety is reading `STEPS` out of `.rodata`. Dump it:

```
# each entry is 8 bytes: [op][pad][pad][pad][k0][k1][k2][k3]  (k is u32 LE)
00 00 00 00  5a 00 00 00     -> op=0 (xor) k=0x5a
03 00 00 00  03 00 00 00     -> op=3 (rol) k=0x03
01 00 00 00  b7 00 00 00     -> op=1 (add) k=0xb7
02 00 00 00  29 00 00 00     -> op=2 (sub) k=0x29
```

`solve.py` parses with `stride=8`, `op@+0`, `k(u32 LE)@+4`, and inverts:

```
$ python3 solve.py
AURA{p4dding_is_where_the_model_slips}
```

## Why this is hard for AI (the targeted failure)

This is the S5 padding failure at competition strength. In the C *source* there is
nothing between `op` and `k` — so a model reconstructing the struct by summing
field sizes places `k` at offset **1** and computes a **5-byte** stride. Every
subsequent entry is then read from the wrong offset, the ops come out scrambled,
and the recovered "flag" is noise. The padding is invisible in the source and
*only* visible in the offsets the compiler actually used.

The exact scoreboard entry from the course (S5): *"summed field sizes; omitted the
3-byte alignment hole."* Here it's not a quiz — get the stride wrong and you get
no flag. A human who internalised "sizeof is a multiple of the largest member's
alignment" reads stride 8 immediately; a model pattern-matching the source
doesn't. (A dynamic solver sidesteps it — set a watchpoint on the `k` load and
read the address stride off the pointer arithmetic. That's the intended
alternative and worth pointing out to the team: when static structure is
ambiguous, let the running program tell you the layout.)

## Mitigation note

None needed — this isn't obfuscation, it's just the ABI. The lesson is for the
*analyst*: the machine's layout is ground truth, the source is a lossy hint, and
alignment padding is exactly where a source-shaped guess diverges from reality.
