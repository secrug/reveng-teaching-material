# Worksheets & Templates

Print-outs the sessions call for, beyond the five reference cards.

---

## Register grid (S2, S4 — "be the CPU" hand-tracing)

One row per instruction; students fill the register state after each. Print a
grid of ~24 rows. Suggested columns:

```
# | instruction | rax | rbx | rcx | rdx | rsi | rdi | rsp | flags(ZF SF CF OF) | notes
--+-------------+-----+-----+-----+-----+-----+-----+-----+--------------------+------
1 |             |     |     |     |     |     |     |     |                    |
2 |             |     |     |     |     |     |     |     |                    |
...
```

Tell students: only fill the registers an instruction *changes* — copying
unchanged values down every row wastes time and hides what moved.

---

## Stack-frame worksheet (S4)

A pre-drawn empty stack, addresses decreasing downward, for hand-drawing frames
alongside the live gdb demo:

```
 high ┌──────────────────────┐
      │                      │  ← caller's frame
      ├──────────────────────┤  ← rbp+8   [               ] return address
      │                      │  ← rbp     [               ] saved rbp
      │                      │  ← rbp-8   [               ]
      │                      │  ← rbp-16  [               ]
      │                      │  ← rbp-24  [               ]
      │                      │  ← rsp     [               ]
 low  └──────────────────────┘
```

---

## Struct-layout worksheet (S5)

A byte ruler for drawing struct layouts and shading padding holes:

```
offset: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
        [  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]...
field:  

offset:16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
        [  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ][  ]...
field:  

sizeof = ______  (multiple of the largest member's alignment!)
padding holes shaded: ____________
```

---

## The RE Notebook (all sessions; the one habit to keep)

The single template carried across all ten sessions and — the hope — for a
career. One page per investigation. This is the deliverable of S9's Lab B and the
"keep this forever" of S10.

```
TARGET: ________________________   DATE: __________
GOAL (one sentence — what am I actually trying to learn?):
________________________________________________________

TRIAGE (the 5 steps):
  what is it: 
  touches:
  says:
  calls:
  entry point for my goal:

HYPOTHESES  (form → predict → test → verdict)
┌────┬─────────────────────┬──────────────────────┬───────────┐
│ #  │ hypothesis          │ prediction if true   │ verdict   │
├────┼─────────────────────┼──────────────────────┼───────────┤
│ 1  │                     │                      │ ✓ / ✗ / ? │
│ 2  │                     │                      │           │
└────┴─────────────────────┴──────────────────────┴───────────┘

EVIDENCE  (the actual observations — register values, offsets, dumps)


DEAD ENDS  (kept on purpose — so I / the next person don't retry them)


OPEN QUESTIONS  (unresolved — carried forward)


AI USED?  where it helped / where it was wrong / how I knew:
```

**Why the notebook matters more than any single answer:** it *is* the method made
visible — form, predict, test, record. It's what makes your work reproducible,
what stops you re-deriving the same thing next week, and what lets you catch a
generator (decompiler or LLM) by having your own evidence trail to check it
against. If a student keeps one thing from the course, it's this.
