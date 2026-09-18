# Brick Wall — Writeup

**Category:** crypto (anti-automation) · **Difficulty:** hard
**Flag:** the accepted input
(reference build: `AURA{symb0lic_execution_hits_a_wall}`)

## TL;DR

The check is a **chained avalanche over 2-byte chunks**. Chunk *i* depends only on
chunk *i* and the previous chunk's hash. So you brute-force **65 536 candidates
per chunk, left to right** — about a million operations, instant — instead of
attacking 36 symbolic bytes at once. A second loop adds a data-dependent branch
per byte purely to flood automated path exploration.

This challenge targets the **automated solver**, not the LLM. It exists to teach
one thing: *understanding collapses a problem that brute force and automation
cannot touch.*

## 1. What it does

```c
uint32_t h = IV;                                  // 0x1234ABCD
for (i = 0; i < NCHUNK; i++) {
    uint16_t c = in[2*i] | (in[2*i+1] << 8);      // 2 bytes at a time
    uint32_t v = mix(c, h, i);
    if (v != TABLE[i]) fail;
    h = v;                                        // <-- CHAINED
}
```

with a murmur-style finalizer:

```c
mix(c, h, i):  x = c ^ (h & 0xFFFF);
               y = x * 0x85EBCA6B;  y ^= y >> 13;
               y = y * 0xC2B2AE35;  y ^= y >> 16;
               return y + h + i * 0x7F4A7C15;
```

Then a second gate:

```c
for each byte b:  if (b & 1) acc += b*3;  else acc ^= b*5;   // one branch per byte
if (acc != ACC_TARGET) fail;
```

## 2. The naive automated attack fails

Point `angr` at it with `explore(find=success)` and it dies, for two independent
reasons — both of them *published* anti-symbolic-execution techniques rather than
accidents:

1. **One-way opaque predicate.** The constraint is a chain of 32-bit
   **multiplications** interleaved with shifts and xors. SMT solvers are
   notoriously weak on multiplication chains; asking Z3 to invert eighteen of them
   composed together is not a query that returns.
2. **Path-explosion predicate.** The checksum loop takes a data-dependent branch
   on every one of 36 symbolic bytes → up to 2³⁶ paths. And it is *not* dead code
   — `acc` is verified — so it can't be pruned away.

A brute-force search over the whole input is 2²⁸⁸. Also not happening.

## 3. The human attack succeeds in seconds

Read the loop and notice the structure: **`h` is fed forward, and the input enters
16 bits at a time.** So once you know `h` going into chunk *i*, the only unknown is
a 16-bit value. Search it:

```python
h = IV
for i, target in enumerate(TABLE):
    for c in range(0x10000):
        if mix(c, h, i) == target:
            out += bytes([c & 0xFF, c >> 8]); h = target; break
```

18 chunks × 65 536 = ~1.2 million `mix` calls. Instant, and each chunk has exactly
one preimage in practice (65 536 candidates mapping into a 32-bit space).

```
$ python3 solve.py
AURA{symb0lic_execution_hits_a_wall}
```

The checksum gate needs no attention at all: once the chunks are right, `acc` is
automatically correct. It only ever existed to punish the machine.

## 4. The honest version of "angr can't do this"

Be straight with the team about this, because overclaiming here would undercut the
whole course. **A skilled angr user can also solve this** — by not being naive:
constrain and solve one chunk at a time, concretising `h` between chunks, exactly
mirroring the manual attack. Symbolic execution is not defeated in principle.

What's defeated is **automation applied without understanding**. The tool only
works once a human has supplied the decomposition — and supplying the
decomposition *is* the solve. That's precisely the course thesis in its
non-LLM form:

> The bottleneck was never the computation. It was knowing how to cut the problem
> so the computation becomes trivial. Nothing delegates that.

Worth pointing out to students that the same asymmetry is why real-world crypto
uses *wide* state and *no* per-chunk verification — leaking an intermediate
comparison per chunk is what makes this tractable at all. A single check over the
whole input at the end would have been genuinely hard for everyone.

## 5. Why it also bites an LLM

Secondary, but real: asked "can this be solved?", a model that recognises the
murmur finalizer tends to answer *"this is a one-way hash, you'd need a preimage
attack — infeasible."* That answer is **wrong**, and it's wrong in the most
expensive way: it stops you working. The chaining plus the 16-bit chunk width is
the detail that makes it trivially feasible, and it's exactly the kind of
structural specific that gets lost when you reason from the category
("it's a hash") rather than from the code. Log that on the AI Scoreboard — a
confident *false negative* ("unsolvable") is a failure mode worth naming, and
students rarely think to distrust one.

## 6. Mitigation note

Both techniques here are used defensively in the wild: obfuscators insert
hash-based and path-explosion opaque predicates specifically to make automated
deobfuscation and symbolic analysis uneconomic. The counters are the ones this
writeup used — decompose the problem, concretise aggressively, and attack
structure rather than constraints.
