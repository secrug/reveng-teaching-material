# Lecture 5 — Data: pointers, arrays, structs, and recovering types

---

## 1. Types do not exist in the binary

Lecture 2 stated that memory has no types. This lecture takes that seriously and
then shows why it does not leave you helpless.

What exists in compiled code is: an address, an access width, and an operation. What
does not exist is any record that a particular eight bytes was a `double`, a
`long`, a pointer to a struct, or three separate things.

And yet type information is recoverable — often precisely. The reason is that the
compiler, having erased the types, still had to generate code that respects them.
Every access encodes the width it operates on. Every array index encodes the element
size. Every struct field access encodes the offset. The hardware demands alignment,
so the compiler inserts padding, and the padding is visible in the offsets.

**Type recovery is inference from a consistency the compiler could not avoid.** That
is this lecture.

---

## 2. Arrays: the scale field

Lecture 2 introduced `[base + index*scale + displacement]` and noted that `scale` is
free information. Now we use it.

```asm
mov eax, DWORD PTR [rdi + rsi*4]
```

A *variable* index, multiplied by 4, added to a base. That is array indexing, and
the element size is 4 bytes. Combined with the 32-bit access width (`eax`,
`DWORD PTR`), the type is an array of some 4-byte thing — `int`, `unsigned`,
`float`, or a 4-byte struct.

```asm
mov rax, QWORD PTR [rdi + rsi*8]
```

Element size 8. This is an array of `long`, `double`, or — very commonly —
**pointers**. If the loaded value is then used as an address, it was an array of
pointers.

Pointer arithmetic in C is written in units of the pointed-to type; in assembly it
is written in bytes. `p + 1` where `p` is `int *` compiles to `p + 4`. That
conversion is done by the compiler and is visible to you: when you see a pointer
incremented by 8 in a loop, the loop is walking an array of 8-byte things.

---

## 3. Structs: constant offsets

A struct field access uses a **constant** displacement with no variable index:

```asm
mov eax, DWORD PTR [rdi]         ; field at +0,  4 bytes
mov rcx, QWORD PTR [rdi+0x8]     ; field at +8,  8 bytes
movzx edx, BYTE PTR [rdi+0x10]   ; field at +16, 1 byte
```

The distinction from an array is the *variable* index. `[rdi + rsi*4]` is
`arr[i]` — the index changes at runtime. `[rdi + 8]` is `s->field` — the offset is
fixed at compile time.

This is a strong signal but not a proof. `arr[2]` with a constant 2 also compiles to
a fixed offset. Usually context resolves it: a sequence of *different* constant
offsets with *different* widths is a struct; a fixed offset used with a varying base
in a loop is an array element.

---

## 4. Padding, and why it is the most useful thing in this lecture

Consider:

```c
struct T {
    int  a;
    char b;
    int  c;
};
```

Naively this occupies 4 + 1 + 4 = 9 bytes. It does not. Compile it and read the
offsets:

```
a → +0
b → +4
c → +8        ← not +5
```

Three bytes between `b` and `c` are unused. This is **padding**, and the compiler
inserted it because the hardware prefers — and on some architectures requires —
that a 4-byte value sit at an address divisible by 4. Placing `c` at offset 5 would
misalign it, so the compiler skips to offset 8.

```
 offset:  0  1  2  3 | 4 | 5  6  7 | 8  9 10 11
 field:  [    a     ]|[b]|[ pad  ]|[    c     ]
```

The rules:

- Each member is placed at an offset divisible by its own alignment requirement
  (usually its size, up to 8).
- The struct's total size is rounded up to a multiple of its largest member's
  alignment, so that arrays of the struct keep every element aligned.

So `sizeof(struct T)` is **12**, not 9 and not 11.

Two reasons this matters more than it looks.

**It is the key to reconstructing a struct correctly.** If you read three fields at
offsets 0, 4 and 8 and write down `int; char; int;` you have it right. If you write
down `int; char; char; char; int;` you have four fields where there were three.
Padding is not a field. It is absence.

**It is invisible in the source and visible in the binary.** This is unusual. Almost
everything else in this course is information the source had and the binary lost.
Padding is the reverse: the C programmer never wrote it, never saw it, and may not
know it exists. The binary shows it plainly in the offsets.

That asymmetry has a consequence we return to at the end.

---

## 5. Arrays of structs

Combining the two ideas gives the pattern that appears constantly in real code:

```asm
lea rax, [rdi + rsi*8]
mov eax, DWORD PTR [rax + rdx*2 + 0x10]
```

More typically you will see a single addressing mode with both a scaled index and a
displacement:

```asm
mov eax, DWORD PTR [rdi + rsi*24 + 0x8]
```

Read this as: base `rdi`, element size **24**, index `rsi`, then field at offset 8
within the element. So `rdi` is an array of a 24-byte struct, and this instruction
reads a 4-byte field 8 bytes into it — `arr[i].field`.

The stride is the `sizeof` of the struct, including its padding. A stride of 24 for
a struct whose fields sum to 20 tells you there are 4 bytes of padding somewhere,
before you have identified a single field.

Note also that scales are limited to 1, 2, 4 and 8. A 24-byte stride cannot be
encoded directly, so the compiler will emit a multiply or a `lea` sequence to
compute the offset first. Seeing `imul rax, rsi, 24` before an array access is the
compiler telling you the element size explicitly.

---

## 6. When you cannot tell

Being honest about ambiguity is a professional skill, and this is the natural place
to practise it.

```asm
mov rax, QWORD PTR [rdi]
mov rcx, QWORD PTR [rdi+8]
```

Two 8-byte reads. This is consistent with:

```c
struct A { long x; long y; };
struct B { long x; void *p; };
struct C { double d; long n; };
struct D { char *s; size_t len; };
```

and several others. The binary genuinely underdetermines the type here.

The correct output is not a guess. It is a **candidate set plus the observation that
would discriminate**:

- If `[rdi+8]` is later dereferenced, it is a pointer — that kills `A` and `C`.
- If either is loaded with `movsd` instead of `mov`, it is a floating-point value —
  that selects `C`.
- If `[rdi]` is passed to `strlen`, it is a `char *` — that selects `D`.
- If `[rdi+8]` is compared against a small integer and used as a loop bound, it is a
  count.

"I do not know yet, but a float load at +0 would settle it" is a better answer than
a confident wrong one. It is also actionable: it tells you exactly what to go and
look for.

---

## 7. Where data lives

Knowing *where* a pointer points tells you a great deal before you read anything it
points at.

| Region | Address shape | What it implies |
|---|---|---|
| `.rodata` | fixed, low | Constants, string literals. **Read-only** — nothing writes here |
| `.data` | fixed, low | Initialised globals. Fixed address for the program's lifetime |
| `.bss` | fixed, low | Zero-initialised globals. Occupies no space in the file |
| stack | high, near `rsp` | Locals. Lifetime is the function call |
| heap | middle, from `malloc` | Dynamic. Lifetime is explicit, and someone must free it |

A pointer into `.rodata` will never be written through — if you see a write, your
identification is wrong. A stack pointer becomes invalid when the function returns,
which is what makes returning a pointer to a local a bug. A heap pointer came out of
`malloc` and has an owner somewhere.

`.bss` is worth one extra sentence because it surprises people: a 10 MB
zero-initialised global array adds 10 MB to the program's memory but nothing to the
file on disk. The file records only "reserve this much, zeroed". This is why a
binary's file size and its memory footprint can differ wildly.

---

## 8. The heap

Dynamic allocation appears in a recognisable shape:

```asm
    mov  edi, 0x20           ; 32 bytes
    call malloc
    mov  QWORD PTR [rbp-0x8], rax   ; keep the pointer
    ...
    mov  rdi, QWORD PTR [rbp-0x8]
    call free
```

The size passed to `malloc` is frequently the `sizeof` of a struct, which gives you
the struct's total size — padding included — before you have identified any fields.
If you then see accesses at offsets 0, 8, 16 and 24 within that allocation, you know
you have found all of it.

When the size is computed rather than constant — `imul rdi, rsi, 24` then `call
malloc` — you are looking at an array allocation, and the multiplier is the element
size.

Following a heap pointer means tracking the value returned in `rax`: where it is
stored, what is passed it, which functions receive it. That is ordinary data-flow
tracing, and it is the main reason to care about which register `malloc` returns in.

---

## 9. Recovering a struct, and proving it

The method, in order:

1. Find every access through the base pointer and record `(offset, width)` pairs.
2. Sort by offset. Gaps that cannot hold a field are padding.
3. Infer each field's type from its width and how it is used.
4. Compute the total size and check it against the stride of an array of the struct,
   or against the argument to `malloc`.
5. **Prove it.**

Step 5 is what separates this from guessing. A recovered struct is a hypothesis
until you use it to make the program do something. If the program parses a config
file matching your layout and accepts it, your layout is right. If it rejects it,
something is wrong — the layout, or a checksum, or a field you misidentified — and
you have learned that too.

For AURA-7's configuration parser, the recovered layout looks like this:

```c
struct aura_config {
    uint32_t magic;         // +0
    uint16_t version;       // +4
    uint16_t flags;         // +6
    char    *device_path;   // +8    (8-byte aligned)
    uint32_t timeout_ms;    // +16
    uint8_t  mode;          // +20
    // 3 bytes padding         +21..23
    uint32_t checksum;      // +24
};                          // sizeof = 28
```

Note `checksum` at offset 24, not 21. The `uint8_t` at +20 is followed by three
bytes of padding so that the 4-byte `checksum` lands on a multiple of 4.

Writing bytes into a file at exactly those offsets and having `auractl` accept the
result is proof. Everything before that is a hypothesis with good evidence behind
it, which is a different and lesser thing.

---

## 10. The blind spot

Struct recovery is the clearest case in this course of an automated failure you can
predict *in advance*, and the reason is §4.

The padding is invisible in the source. Training material — every C tutorial, every
codebase, every textbook — shows structs as a list of fields with nothing between
them. A tool that has learned what structs look like has learned the *source* form,
where `mode` is immediately followed by `checksum`.

So when asked to reconstruct a struct from a disassembly, the systematic error is to
sum the field sizes and place the next field there. `magic`(4) + `version`(2) +
`flags`(2) + `device_path`(8) + `timeout_ms`(4) + `mode`(1) = 21, so `checksum` goes
at 21.

The binary says 24.

What makes this instructive rather than merely another mistake is the direction of
the asymmetry. Usually a tool fails because information was destroyed and it guessed.
Here, information the *source never contained* is sitting in plain view in the
binary, and the tool misses it because its model of "what a struct looks like" comes
from the source.

The check is immediate: find the instruction that accesses the field and read the
offset off it. `[rdi+0x18]` is offset 24. That is not an inference, it is a number
in an instruction.

Predicting a specific failure before you look is the practical form of understanding
a tool's limits. You will do this repeatedly for the rest of the course.

---

## Summary

- Types do not exist in the binary. Offsets and access widths do, and they are
  enough.
- Variable index × scale &rarr; array, and the scale is the element size.
- Constant displacement &rarr; struct field, usually.
- Padding is inserted for alignment; struct size rounds up to the largest member's
  alignment. `sizeof` is not the sum of the fields.
- Padding is invisible in source and visible in the binary — an asymmetry that
  matters.
- An array-of-struct stride is the struct's full size, padding included. A
  `imul rsi, 24` before an access states the element size outright.
- When the binary underdetermines the type, produce a **candidate set and the
  discriminating observation**, not a confident guess.
- Where a pointer points — `.rodata`, `.data`, `.bss`, stack, heap — constrains what
  it can be.
- `malloc`'s size argument often gives you a struct's total size before you have
  found a single field.
- A recovered struct is a hypothesis until you use it to make the program do
  something.
- The systematic tool error here is **dropped padding**. Predict it, then read the
  offset off the instruction.

## Reading

- *Computer Systems: A Programmer's Perspective*, §3.8–3.9 — arrays, structs,
  alignment.
- Exercise: define three structs with deliberate padding, predict each `sizeof`,
  check with a one-line program, then read the offsets back out of the assembly.
