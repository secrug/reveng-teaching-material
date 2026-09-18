# Session 5 — Data: pointers, arrays, structs, and type recovery

**The one idea:** types don't exist in the binary — only offsets and access
sizes do. But offsets and access sizes are enough to reconstruct the types,
because the compiler had to be consistent. Type recovery is inference from a
consistency it couldn't avoid.

---

## Outcomes

1. Read pointer arithmetic in asm and derive element size from the `*scale`.
2. Tell an array access from a struct-field access, and say when you can't.
3. Reconstruct a `struct` — including padding — from field offsets alone.
4. Locate whether data lives in `.rodata`, `.data`, `.bss`, the stack, or the
   heap, and know what each implies.
5. Recognise a heap pointer and the shape of `malloc`/`free` usage.
6. Find the alignment-padding error in a model's proposed struct.

---

## Prep checklist

- [ ] `s05/` pack: `access`, `layouts` (two structs, same accesses), `storage`,
      `heaplife`, and the flagship `configparse` + a sample config file
- [ ] Reference card **#2/#3** in hand
- [ ] Board space for struct-layout boxes with byte offsets
- [ ] Casts: `s05-demo1.cast` (struct recovery), `s05-demo2.cast` (ambiguity)

---

## 0:00 — Warm-up (15 min)

1. `[rdi + rsi*8]` — what does the `*8` tell you about `rdi`?
2. Which register holds arg 3? The return value?
3. `rbx` is pushed in the prologue — what does that tell you the function intends
   to do?
4. From the AURA-7 map: name one command handler and its recovered arity.
5. Read-before-write of `rsi` means what, exactly?

Q1 is the bridge into today — the `*scale` field was flagged in S2 and S4 as
"you'll use this for types later." Later is now.

---

## 0:15 — Cold open (10 min)

On screen, two access sequences into the same base pointer `rdi`:

```asm
  mov  eax, DWORD PTR [rdi]          ; +0,  4 bytes
  mov  rcx, QWORD PTR [rdi+0x8]      ; +8,  8 bytes
  movzx edx, BYTE PTR  [rdi+0x10]    ; +16, 1 byte
  mov  esi, DWORD PTR [rdi+0x14]     ; +20, 4 bytes
```

**Question:** write the C struct. Exactly. Including any padding.

Written prediction. The trap is +0x10 to +0x14: why is a 1-byte field followed by
the next field 4 bytes later? Resolved at 2:55 — it's the drill's whole point.

---

## 0:25 — Teach A: memory has no types (35 min)

### A1 — The scale field is a gift (10 min)

Back to addressing modes, now read for meaning:

```
 [rdi + rsi*1]   → array of bytes,   rsi is the index
 [rdi + rsi*4]   → array of ints,    rsi is the index
 [rdi + rsi*8]   → array of longs / pointers, rsi is the index
 [rdi + 0x8]     → field at offset 8 (constant → struct-ish)
 [rdi + rsi*8 + 0x10]  → array of 8-byte things, based at rdi+16
```

> "Variable index times a scale? Array — and the scale is the element size, handed
> to you free. Constant offset? Probably a struct field. The compiler encoded the
> element size into the instruction because the machine needs it, and in doing so
> it told you a type it had otherwise erased."

### A2 — Structs are just offsets, and padding is the tell (13 min)

Live on Compiler Explorer. Define:

```c
struct T { int a; char b; int c; };
```

Access `.a`, `.b`, `.c` and read the offsets off the asm: `+0`, `+4`, `+8`.

> "Watch. `b` is one byte at offset 4. `c` is at offset 8 — not 5. Three bytes are
> *wasted* between them. That's **padding**. The compiler inserts it so `c`, a
> 4-byte int, sits on a 4-byte boundary — the hardware prefers aligned accesses.
>
> This padding is invisible in your C source. It is *visible* in the offsets. And
> it is" — foreshadow hard — "the single most reliable thing a language model
> gets wrong, because in the source there's nothing to see, so it counts field
> sizes and forgets the holes."

Draw the box on the board, bytes labelled 0–11, the 5/6/7 hole shaded:

```
 offset:  0  1  2  3 | 4 | 5  6  7 | 8  9 10 11
 field:  [    a     ]|[b]|[ pad  ]|[    c     ]
```

Rule, onto their notes: **struct size is a multiple of its largest member's
alignment.** `sizeof(struct T)` is 12, not 9.

### A3 — Ambiguity, and where data lives (12 min)

**The honest part.** Show `layouts`: one access pattern, `[rdi]` then `[rdi+8]`,
consistent with:

```c
struct A { long x; long y; };        // two longs
struct B { long x; void *p; };       // a long and a pointer
struct C { double d; long n; };      // reads via movsd would disambiguate
```

> "You cannot always tell. Sometimes the binary genuinely underdetermines the
> type, and the honest output is a *set* of candidates plus the observation that
> would decide between them. 'I don't know yet, but a float load at +0 would
> settle it' is a professional answer. 'It's definitely two longs' when you can't
> see how it's used is not."

Then storage classes, live with `readelf`/`gdb` on `storage`:

| Where | Address shape | Meaning |
|---|---|---|
| `.rodata` | fixed, low | constants, string literals — read-only |
| `.data` | fixed, low | initialised globals |
| `.bss` | fixed, low | zero-init globals (takes no file space) |
| stack | high, near `rsp` | locals, per-call |
| heap | `malloc`'d, mid | dynamic, lives across calls |

> "*Where* a pointer points tells you what kind of thing it is before you read a
> single byte of it. A pointer into `.rodata` won't be written. A heap pointer
> came from `malloc` and someone has to `free` it. Address ranges are type
> information too."

Heap shape in 60 seconds on `heaplife`: `call malloc` → `rax` is your object;
the value in `rax` gets stored somewhere and passed around; eventually `free`.
"Heap pointers are the ones that came out of `rax` after `malloc`. Learn to spot
that call and follow its result."

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: reading data (40 min)

Full spec: [`labs/s05-lab.md`](../labs/s05-lab.md).

- **Core** — `access`: three functions walking data structures. For each, say
  array or struct, element/field sizes, and draw the layout.
- **Stretch** — reconstruct the struct in `access` fn 3, padding included, and
  compute `sizeof`. Verify with gdb by dumping an instance.
- **Boss** — `layouts`: produce the candidate set for the ambiguous access and,
  for each candidate, the single observation that would confirm or kill it.
  (Explain-back — this is the "know what you don't know" tier.)

---

## 1:50 — Teach B: live struct recovery on AURA-7 (25 min)

**Target:** `configparse`, the flagship — AURA-7's config reader.

Reverse the config struct live, from the parser's accesses. **Scripted wrong
turn:** early on, read three consecutive 4-byte accesses and declare "array of
four ints" — then hit a `[rdi+0x10]` that's accessed as a **pointer** (passed to
`strlen`). Stop.

> "That kills 'array of ints' — element 4 of an int array isn't a string pointer.
> So it's a struct, and I over-read the pattern. Back up."

Rebuild it properly, offset by offset, drawing the box on the board and shading
padding holes as they appear. Land on something like:

```c
struct aura_config {
    uint32_t magic;        // +0
    uint16_t version;      // +4
    uint16_t flags;        // +6
    char    *device_path;  // +8   (8-byte aligned — note the gap if any)
    uint32_t timeout_ms;   // +16
    uint8_t  mode;         // +20
    // 3 bytes padding      +21..23
    uint32_t checksum;     // +24
};                          // sizeof = 28? 32? make them compute it
```

Then the payoff that proves it: **generate a config file matching this layout and
feed it to `auractl`.** If the program accepts it, the struct is right. If it
rejects it, the struct — or the checksum algorithm — is wrong, and that's a new
open question.

> "This is the difference between a decompiler's guess and knowledge. I didn't
> assert the struct. I *used* it to make the program do something, and it worked.
> That's proof. Everything before that was a hypothesis."

Add the struct to the AURA-7 MAP on the board.

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: prove the struct (30 min)

Students take the struct from Teach B (provided, so nobody's blocked) and:
- **Core:** write it as C and compute `sizeof` with padding correct.
- **Stretch:** hand-craft a config file — bytes at the right offsets — that
  `auractl` accepts. This is the flagship deliverable of the whole session.
- If the checksum blocks them: that's the open question for S9. Note it, move on.

Seed the drill: **"ask a model for the `aura_config` struct from the parser
disassembly. Keep it."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** The model's struct, almost always missing a hole:

```c
struct aura_config {         // model output
    uint32_t magic;
    uint16_t version;
    uint16_t flags;
    char *device_path;
    uint32_t timeout_ms;
    uint8_t  mode;
    uint32_t checksum;       // model puts this at +21
};
```

1. *State it.* "Model says `checksum` is at offset 21."
2. *What would falsify it?* — the actual access. Find where the parser reads the
   checksum and read the offset off the instruction.
3. *Observe.* `objdump`/gdb: `[rdi+0x18]` — offset **24**, not 21. There are 3
   padding bytes after `mode` that the model omitted.
4. *Verdict.* **Wrong — dropped the alignment padding.** Reason: in the C source
   there is nothing between `mode` and `checksum`, so the model summed field
   sizes (21) and never inserted the hole the compiler inserts. Exactly the
   failure predicted in A2. This is a *systematic* blind spot, not bad luck —
   note that in the reason column.

> "We called this one before it happened. That's the goal: not 'AI is sometimes
> wrong' but 'AI is wrong *here*, for *this reason*, and I can predict it.' That
> prediction is what your fundamentals buy you."

**Cold-open reveal.** The +0x10 → +0x14 gap in the morning's struct: a 1-byte
field at +0x10, then 3 bytes of padding, then a 4-byte field forced to +0x14 for
alignment. Same phenomenon. It was there all along, on the board.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 5 | `aura_config.checksum` is at offset 21 | ✗ Wrong (padding) | Summed field sizes; omitted the 3-byte alignment hole after `mode`. Real offset 24. **Systematic** — invisible in source, so predicted in advance |

---

## Lecturer notes

**Padding is the star and it must land.** If one thing survives to S9, it's "the
offsets show padding the source doesn't." Draw every hole. Shade it. Compute
`sizeof` out loud every time.

**Ambiguity discomforts students who want one right answer.** That discomfort is
the lesson — the candidate-set answer is *more* correct than a confident wrong
one. Praise the student who says "I can't tell yet, but here's what would tell
me." Loudly.

**The checksum will probably block the config-forging task.** Fine — that's a
planned S9 thread, not a failure. Make sure students *record* it rather than
grinding on it. Managing an open question is itself a S9 skill previewed here.

**Running long.** Cut Boss tier, then the heap segment of A3 (but keep "heap
pointers come out of `malloc` in `rax`" — one sentence, needed for S7). Protect
the live struct recovery and the config-forging proof.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-5)

- **Read:** CS:APP §3.8–3.9 (30 min) — arrays, structs, alignment.
- **Do:** define three structs with deliberate padding; predict each `sizeof`;
  check with a one-line program; then read them back off the asm.
- **Crackme:** crackmes.one difficulty 2, any "serial"/"format" challenge that
  parses structured input.
- **Self-check:** 5 questions, answers included.
