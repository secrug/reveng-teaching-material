# Overrun — Writeup

**Category:** pwn · **Difficulty:** medium · **Flag:** server-side `flag.txt`
(per-instance)

## TL;DR

The command-length field is a **signed** 32-bit int. The bounds check
`if (len > 64) reject` only stops large *positive* lengths; a negative length
sails through and is then passed to `fread()` as a `size_t`, becoming enormous.
Send length `0xFFFFFFFF` (= −1), then a payload that overflows the 64-byte stack
buffer and overwrites the return address with `&unlock` (ret2win).

## 1. The bug

```c
int len = read_len_be32();          // SIGNED
if (len > 64) { puts("too long"); return; }
fread(buf, 1, (size_t)len, stdin);  // (size_t)(-1) == 0xffffffffffffffff
```

`len = -1` passes `-1 > 64` (false), then `(size_t)(-1)` at the `fread` is
`SIZE_MAX`, so `fread` will happily read as much as you send into a 64-byte
buffer. No canary (`-fno-stack-protector`) → the saved return address is
overwritable. No PIE (`-no-pie`) → `unlock()` is at a fixed address.

## 2. Exploit

`unlock()` opens `flag.txt` and prints it, and is never called normally — a
textbook **ret2win**.

```
payload = b"A"*72 + p64(ret_gadget) + p64(&unlock)
```

- **72** = 64 (buffer) + 8 (saved `rbp`) to reach the return slot.
- **ret_gadget**: a bare `ret` before `unlock`, to fix 16-byte stack alignment so
  the `movaps` inside `unlock`'s `printf` doesn't fault — the single most common
  "my ret2win segfaults" gotcha. `solution/exploit.py` inserts it automatically.

```
$ ./exploit.py                 # local
$ ./exploit.py 10.0.0.5 9007   # remote
AURA{...}
```

## 3. What's verified where

- **Verified on the authoring machine** (`src/verify_reach.py`, no compiler
  needed): the signedness bypass — `0xFFFFFFFF` decodes to −1, passes `>64`, and
  becomes `SIZE_MAX` at the `fread`. The framing the exploit sends is correct.
- **Verified on build** (`healthcheck.sh`, your Linux toolchain): the offset (72)
  is re-confirmed with a `cyclic` pattern + corefile, `&unlock` is read from the
  binary, and the exploit is run against the live process until it prints the
  flag. **A pwn exploit is not "done" until this passes on the actual binary** —
  the source-derived 72 is a strong prediction, not a guarantee (compiler
  version/alignment can shift it).

## 4. Why this is hard for AI (the targeted failure)

Two layers, both on the scoreboard.

1. **The bug hides behind a check that looks correct.** A model skimming this
   sees `if (len > 64) reject` and concludes "length-validated, safe." The vuln is
   the *type* of `len`, not the absence of a check — the signed/unsigned confusion
   from the course's S3/S5 material, weaponised. Recognising it requires reasoning
   about the implicit `int → size_t` conversion at the `fread`, not
   pattern-matching "has a bounds check → safe."
2. **Memory-corruption exploitation is the benchmark-hard category.** Public
   evaluations show agents need substantial scaffolding to move on
   buffer-overflow tasks at all, and the fiddly, layout-dependent details — exact
   offset, the alignment `ret` gadget — are exactly where they stumble. The
   alignment gadget especially: it's invisible in the source, learned only from
   watching the exploit crash and knowing *why*.

The human path is the S4/S7 method: spot the signedness, confirm the overflow
reaches the return address (`cyclic`), pick a ret2win target, add the alignment
gadget when the first attempt faults. A human directing an AI — "the length is
signed; send −1 and check where a cyclic pattern lands in RSP" — converges fast.

## 5. Mitigations

Use an unsigned type for lengths (or reject `len < 0` explicitly); bound-check
against the buffer size, not a magic constant; compile with the stack protector
(`-fstack-protector-strong`) and PIE + full RELRO. Any one of these breaks the
exploit; the combination is standard hardening the challenge deliberately omits.
