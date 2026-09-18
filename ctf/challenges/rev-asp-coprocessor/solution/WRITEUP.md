# The Coprocessor — Writeup

**Category:** rev · **Difficulty:** hard · **Flag:** the accepted input
(reference build: `AURA{a_transport_triggered_l00p_w1th_branches}`)

## TL;DR

The full AURA Signal Processor: a **transport-triggered architecture** (only
`MOV`/`MOVI`/`HALT`) with **function units** whose *write* ports trigger
computation, and **control flow** via program-counter ports. The flag checker is
a compact **loop** with a conditional branch on end-of-input. Recover the machine,
recover the loop's per-byte transform, invert it.

This is `signal-lock`'s big sibling: same "moving data is computing" trick, but
now with a real loop and a branch instead of an unrolled straight line.

## 1. The machine

Three opcodes only:

```
0x00 HALT | 0x01 MOV dst,src | 0x02 MOVI dst,imm
```

No ADD/XOR/CMP/JMP opcodes exist. So — as in `signal-lock` — reverse what
`read(port)`/`write(port)` *do*. Recovered port map:

```
0x10 INPUT (read: next byte)     0x13 EOF (read: 1 if input exhausted)
0x11 CHECK (write: compare to expected[out++])
0xA0/1/2 ADD .A / .B(trigger A+B) / .R
0xB0/1/2 XOR .A / .B(trigger A^B) / .R
0xC0/1/2 ROL .V / .N(trigger rol8(V,N)) / .R
0xE0/1/2 AND .A / .B(trigger A&B) / .R
0xD0/1/2 CMP .A / .B(trigger: FLG = A==B) / FLG
0xF0 JMP  (write target -> pc = target)            <- control flow!
0xF2 JZF  (write target -> if FLG: pc = target)
```

The two novelties over `signal-lock`: the **CMP unit** produces a flag, and
**writing to `0xF0`/`0xF2` is a jump**. Recognising that a *data move to a port*
is a branch is the crux — there is no `jmp` mnemonic to grep for.

## 2. The loop

Decoding the ~28-instruction program gives:

```
R2 = K2                          ; running additive term
loop:
  CMP.A = EOF ; CMP.B = 1        ; FLG = (input exhausted?)
  JZF done                       ; if so, stop
  R0 = INPUT                     ; c
  R0 = R0 ^ K1                   ; via XOR unit
  R0 = rol8(R0, R1 & 7)          ; ROL unit; rotate amount from AND unit (R1 & 7)
  R0 = R0 + R2                   ; ADD unit
  R0 = R0 ^ K3                   ; XOR unit
  CHECK = R0                     ; compare to expected[i]
  R2 = R2 + K4                   ; additive term grows each iteration
  R1 = R1 + 1                    ; index
  JMP loop
done: HALT
```

`R1` is the position `i`; `R2` is `K2 + i*K4` (an arithmetic progression the loop
maintains, since the machine has no multiply). So the per-byte transform is:

```
t = ( rol8(c ^ K1, i&7) + (K2 + i*K4) ) & 0xFF ^ K3
```

with `K1=0x5A, K2=0x1B, K3=0x3C, K4=0x11` read straight from the `MOVI`
immediates.

## 3. Invert

Every stage is reversible:

```
u = t ^ K3 ; u = (u - (K2 + i*K4)) & 0xFF ; u = ror8(u, i&7) ; c = u ^ K1
```

```
$ python3 solve.py            # inverts expected[] dumped from the binary
AURA{a_transport_triggered_l00p_w1th_branches}
```

(Dynamic route: breakpoint on the `CHECK` write at port `0x11`, feed `AAAA…`, and
read `R0` each hit to see the transform without decoding a single opcode — then
invert.)

## 4. Why this is hard for AI (the targeted failure)

Same core as `signal-lock`, escalated (TM-A). Three stacked obstacles:

1. **Novel machine model, no silhouette to recall.** A transport-triggered
   architecture has no `switch(opcode)` with 20 arithmetic cases. A model primed
   on stack/register VMs hunts for opcodes that don't exist and misreads unit
   writes as plain stores.
2. **Control flow hidden as data movement.** The branch is `MOVI 0xF2, target`.
   Nothing looks like a jump. Recovering that the PC is a writable port is
   reasoning, not recall — and it's essential, because without it the "program" is
   just a list of moves with no loop.
3. **Long inference chain.** Machine model → unit semantics → loop structure →
   position term (`K2 + i*K4`, not `i*const`) → invert. Any early error propagates;
   LLMs lose coherence across chains like this, which is exactly the benchmark
   finding (novel + multi-step = where agents stall).

Intended winning path = the course method, and it rewards human+AI: a human who
recognises "there are only three opcodes, so computation must be in the ports"
can direct a model to grind out the port map and the loop, then supplies the
inversion. That configuration beats an unguided agent, which is the whole thesis.

**Host note:** re-verify before each deploy (unguided agent should stall on the
TTA classification and the PC-as-port branch). If a future model one-shots it,
escalate to `pwn/asp-escape` territory: interleave the pipeline across
non-adjacent instructions, add unused decoy units, or nest a second ASP. Record
where the wall moved.

## Mitigation note

Unusual execution models are a legitimate anti-analysis technique (they raise the
analyst's cost and defeat pattern-matching), and moving the secret out of static
data — here, `expected[]` is derived per instance — blunts trivial extraction.
The standard counter is dynamic tracing, which collapses the whole abstraction in
minutes; serious protections therefore add anti-debug and integrity checks, the
subject of the S9 material and the pwn-track escalation.
