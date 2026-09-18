# Signal Primer — Writeup

**Category:** rev · **Difficulty:** intro · **Flag:** the accepted input
(reference build: `AURA{w4rmup_the_machine_is_good_at_this}`)

## TL;DR

Each flag byte is `rol8(c, 3) ^ KEY[i % len(KEY)]`, compared to a stored table.
The key is an ASCII string sitting in `.rodata` (`strings` finds it). Invert:
`c = ror8(t ^ KEY[i%kl], 3)`.

## Solve

```
$ strings warmup-decoder | grep -i aura
AURA-SIGNAL-KEY                 # <- the key, in plaintext
$ ./warmup-decoder
AURA{test}
nope.
```

The decompiled `main` is a single loop: `rol8(input[i],3) ^ KEY[i%kl]` compared to
`expected[i]`. Both operations are invertible. `solve.py` reads `expected[]` from
the binary and inverts:

```
$ python3 solve.py
AURA{w4rmup_the_machine_is_good_at_this}
```

## Why this one is *for* AI (the calibration lesson)

This challenge is deliberately easy for an LLM — a rotate-and-XOR with a visible
key is a shape it has seen ten thousand times, and it will one-shot it. **That is
the point.** Before the team spends effort resisting AI on the hard challenges,
they should feel, concretely, what AI is genuinely *good* at:

- recognisable transforms (`rol`/`xor`/standard encodings),
- with public precedent (this is 90% of intro-tier rev),
- where the key material is present and readable.

The professional move here is **not** to hand-reverse it for pride. It's to let
the machine do it in ten seconds, verify the recovered flag actually unlocks the
binary (evidence!), and save your effort for `signal-lock` / `asp-coprocessor`,
where recall fails and the machine stalls. Knowing *which* problems to delegate is
half the skill this suite trains. Log this one on the AI Scoreboard as a **win**
for AI — the column needs wins in it, or the lesson is just propaganda.

## Mitigation note

A visible key in `.rodata` is the canonical "don't do this" of software
licensing. The `mirror` challenge shows the first real countermeasure (don't store
the key material in the clear); `crypto/aura-license` shows what a serious
custom cipher looks like.
