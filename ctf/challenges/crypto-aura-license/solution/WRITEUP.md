# Counterfeit — Writeup

**Category:** crypto (RE crossover) · **Difficulty:** medium · **Type:** keygen-me
**Flag:** printed by the binary when fed a valid licence
(reference build: `AURA{bf3933ce0f32d3df}`)

## TL;DR

The validator decrypts your 8-byte licence with **ALC-64**, an original 16-round
Feistel cipher, and requires the plaintext to equal `"AURA-LIC"`. A Feistel is a
bijection, so **exactly one** licence works. You can't search for it (2⁶⁴) — you
have to recover the cipher and *encrypt* the magic plaintext yourself. That's a
real keygen.

## 1. Triage

```
$ ./aura-license
AURA-7 licence: 0011223344556677
Licence rejected.
$ strings aura-license | head
AURA-7 licence:
Malformed licence.
Licence rejected.
Licence valid. AURA{
AURA-LIC              <- the magic plaintext, sitting in .rodata
```

`"AURA-LIC"` is 8 bytes — exactly one block. And there's a 256-byte table in
`.rodata`. So: block cipher, 64-bit block, byte substitution somewhere.

## 2. Recover ALC-64

Reading `main` → `alc_decrypt`:

```c
L = ld32(b); R = ld32(b+4);                 // 32-bit halves, little-endian
for (i = ROUNDS-1; i >= 0; i--) {           // ROUNDS == 16
    t = R ^ F(L, ks[i]);
    R = L;
    L = t;
}
```

That is a **Feistel network** run backwards. The round function:

```c
F(R, k):  x = rotl32(R ^ k, 7);
          x = sbox_bytes(x);                // SBOX applied to each of 4 bytes
          return x + rotl32(k, 11);
```

And the key schedule is **not** the master key chopped into words:

```c
schedule(m, ks):  st = little-endian u64 load of the 8-byte KEY
                  for i in 0..15: st = st*6364136223846793005 + 1442695040888963407
                                  ks[i] = st >> 32
```

A 64-bit LCG. Dump the three pieces from `.rodata`: `SBOX` (256 bytes), `KEY`
(8 bytes), `MAGIC` (8 bytes).

## 3. Forge

Because decryption is `Feistel⁻¹`, the valid licence is just
`encrypt(MAGIC, key_schedule(KEY))`. Implement the forward direction —
`(L,R) → (R, L ^ F(R, ks[i]))` for 16 rounds — and run it once:

```
$ python3 solve.py
licence: bf3933ce0f32d3df
AURA{bf3933ce0f32d3df}

$ ./aura-license
AURA-7 licence: bf3933ce0f32d3df
Licence valid. AURA{bf3933ce0f32d3df}
```

## 4. Why this is hard for AI (the targeted failure)

This is the S9 scoreboard entry — *"right genre, wrong specifics"* — built into a
challenge where wrong specifics produce **no flag at all**.

ALC-64 is designed to *look* like something a model knows cold: a 16-round Feistel
on 64-bit blocks with 32-bit halves is TEA/XTEA's silhouette exactly. Ask a model
"what cipher is this?" and it will very confidently answer "TEA-like" — and then,
in the same breath, reach for the things that travel with that answer:

| The model's recalled assumption | The reality here |
|---|---|
| delta constant `0x9E3779B9` | there is no delta; the schedule is an LCG |
| key = master split into 4 words `k[0..3]` | 16 round keys, each the **top 32 bits** of successive LCG states |
| round function is shift/add/xor only | there's a **custom 256-byte S-box** in the middle |
| a standard (e.g. AES) S-box | an original permutation you must dump byte-for-byte |

Every one of those is a plausible generalisation from the shape, and every one
yields a licence the binary rejects. There is no partial credit: the cipher is a
bijection, so a single wrong constant gives you a completely different 8 bytes.

The only path that works is the unglamorous one the course drills: **read what's
actually there.** Dump the real S-box, read the real schedule off the
disassembly, transcribe the real round function. A human directing a model —
"don't tell me what it resembles; transcribe `F` line by line and dump me 256
bytes at that address" — gets it quickly. A model left to pattern-match writes
beautiful, confident, wrong TEA.

**Verification advice:** this challenge is *self-checking* in a way that makes the
lesson vivid — you know instantly whether your recovered cipher is right, because
the licence either opens the gate or doesn't. Encourage the team to log the first
attempt on the AI Scoreboard: ask a model for a keygen from the decompilation and
see which of the four assumptions above it imports.

## 5. Mitigation note (the defender's view)

Everything that makes this annoying to reverse is also *bad security practice* in
one specific way: **the key is in the binary.** ALC-64's obscurity buys time
against an analyst, nothing more — once the S-box, schedule and round function are
transcribed, the scheme is fully broken and every licence in the world can be
forged. That's the real lesson of offline licence checks, and it's why they're
backed by server-side validation in practice.

Note also what the design does *right* for a CTF and wrong for production: rolling
your own cipher is the classic mistake. ALC-64 has had no cryptanalysis; it is
almost certainly weak against differential attacks with a fraction of the effort
spent above. "It looks like a cipher" is not a security property.
