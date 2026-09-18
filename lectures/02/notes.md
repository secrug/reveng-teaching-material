# Lecture 2 — The machine: registers, memory, and instructions

---

## 1. The processor is a state machine

A CPU has a complete, finite state, and every instruction is a function from that
state to a new state. Nothing else is happening. There is no hidden mechanism, no
interpretation layer, no notion of a program in the sense you have in mind when you
write one.

On x86-64 the state consists of:

- **Sixteen general-purpose registers**, each 64 bits wide.
- **The instruction pointer**, `rip`, holding the address of the next instruction.
- **A flags register**, recording facts about the last arithmetic result.
- **Memory**, a single flat array of bytes.

That is the whole machine, for our purposes. Three consequences are worth stating
before we go further, because each one contradicts an intuition carried over from
writing C.

**Memory has no types.** A byte is a byte. `int`, `double`, `char *` and `struct
account` do not exist at this level. They were fictions the compiler maintained
while compiling and then discarded. What remains is: an address, a width, and an
operation. Recovering those fictions is what Lecture 5 is about.

**There are no variables.** A variable is a name the compiler assigned to a
register or a stack location. After compilation there is a register or a stack
location, and no name.

**`rip` is an ordinary register that usually increments.** Control flow is nothing
more than writing a different value into it. Almost everything interesting in both
reverse engineering and security comes from the word "usually".

---

## 2. The register file

The sixteen registers are `rax`, `rbx`, `rcx`, `rdx`, `rsi`, `rdi`, `rbp`, `rsp`,
and `r8` through `r15`.

The first eight have names inherited from the 16-bit 8086 of 1978, where they had
dedicated purposes: `ax` was the *accumulator*, `cx` the *counter*, `si` and `di`
the *source* and *destination index* for string operations. On x86-64 these are
mostly historical. `rax` is not special to the hardware in the way its name
suggests.

Two of them do retain meaning by convention rather than by hardware:

- **`rsp`** — the stack pointer. Points at the top of the stack. Modified
  implicitly by `push`, `pop`, `call` and `ret`. Lecture 4.
- **`rbp`** — the frame pointer, by convention. Also Lecture 4.

The remaining registers are general. Which one holds what is decided by the
compiler, except where the calling convention constrains it — that constraint is
what makes function signatures recoverable, and it is also Lecture 4.

---

## 3. Operand sizes, and the one rule you must memorise

Each register can be accessed at four widths. For `rax`:

```
 63                    31        15     7    0
 ├──────────────────────┼─────────┼──────┼────┤
 │                     rax                    │   64-bit
                        │        eax          │   32-bit
                                  │    ax     │   16-bit
                                        │ al  │   8-bit
```

The same pattern applies throughout: `rbx`/`ebx`/`bx`/`bl`, `rsi`/`esi`/`si`/`sil`,
`r8`/`r8d`/`r8w`/`r8b`.

Now the rule, which is arbitrary, which you cannot derive, and which you must know:

> **Writing to a 32-bit register zeroes the upper 32 bits of the full register.
> Writing to a 16-bit or 8-bit register leaves the upper bits unchanged.**

Watch what that does:

```asm
mov rax, 0xffffffffffffffff   ; rax = 0xffffffffffffffff
mov eax, 1                    ; rax = 0x0000000000000001   ← upper half zeroed
mov ax,  2                    ; rax = 0x0000000000000002   ← upper bits preserved
mov al,  3                    ; rax = 0x0000000000000003   ← upper bits preserved
```

In the second line, writing 1 to a 32-bit register cleared the top half. In the
third and fourth, writing to the narrower registers did not.

There is no principle here. It was a decision AMD made when designing the 64-bit
extension, for reasons concerning instruction encoding efficiency: zero-extension
avoids needing a separate prefix for the common case. The 16- and 8-bit forms kept
the old behaviour for backward compatibility.

This rule is the single most common cause of a hand-trace disagreeing with reality,
and — for reasons we come back to at the end — it is also a reliable way to catch
an automated analysis being wrong.

---

## 4. Memory

Memory is one flat array of bytes, indexed by address. There is no structure
imposed by the hardware: no objects, no boundaries, no types. A 64-bit address
space is available, though current implementations use 48 bits.

Two operations exist: **load** (memory to register) and **store** (register to
memory). x86 expresses both with `mov`, distinguished by which operand is in
brackets.

```asm
mov rax, [rbx]     ; LOAD:  rax = the 8 bytes at address rbx
mov [rbx], rax     ; STORE: write rax's 8 bytes to address rbx
```

The width of the access is determined by the register, or stated explicitly when
ambiguous:

```asm
mov eax,  [rbx]              ; load 4 bytes
mov al,   [rbx]              ; load 1 byte
mov DWORD PTR [rbx], 5       ; store 4 bytes of immediate 5
mov BYTE PTR  [rbx], 5       ; store 1 byte
```

Multi-byte values are stored little-endian, as established in Lecture 1: the value
`0x11223344` occupies four consecutive bytes as `44 33 22 11`.

Loading a narrow value into a wide register raises the question of what fills the
upper bits, and the answer depends on whether the value is signed:

```asm
movzx rax, BYTE PTR [rbx]    ; zero-extend: upper bits become 0
movsx rax, BYTE PTR [rbx]    ; sign-extend: upper bits copy the sign bit
```

This distinction matters more than it looks. `movzx` of the byte `0xFF` gives 255;
`movsx` of the same byte gives −1. The instruction the compiler chose tells you
whether the source variable was signed — information the type system carried and
then discarded. This is the first example of the Lecture 1 principle in action:
the compiler had no choice about which instruction to emit, so the instruction
reveals something it otherwise erased.

---

## 5. The instructions worth knowing

x86-64 has well over a thousand instructions. About twenty account for the
overwhelming majority of compiled code.

| Instruction | Effect |
|---|---|
| `mov d, s` | `d = s` |
| `movzx` / `movsx` | move with zero- / sign-extension |
| `lea d, [expr]` | `d = the address expr computes` — see §7 |
| `add` / `sub` | arithmetic |
| `imul` | signed multiply |
| `and` / `or` / `xor` / `not` | bitwise |
| `shl` / `shr` / `sar` | shift left / logical right / arithmetic right |
| `cmp a, b` | compute `a - b`, set flags, **discard the result** |
| `test a, b` | compute `a & b`, set flags, **discard the result** |
| `push` / `pop` | stack (Lecture 4) |
| `call` / `ret` | function call and return (Lecture 4) |
| `jmp` | unconditional jump |
| `jcc` | conditional jump (Lecture 3) |
| `nop` | do nothing |

Two idioms appear so often they should be read as single units rather than decoded:

**`xor eax, eax`** sets `eax` to zero. Anything XORed with itself is zero. The
compiler prefers this to `mov eax, 0` because the encoding is two bytes instead of
five. It is not obfuscation; it is ubiquitous.

**`test rax, rax`** asks "is `rax` zero?". ANDing a value with itself leaves it
unchanged, so the only useful output is the flags — specifically the zero flag.
The compiler prefers this to `cmp rax, 0` for the same encoding-size reason.

---

## 6. Addressing modes

The general form of a memory operand is:

```
[ base + index*scale + displacement ]
```

where `base` and `index` are registers, `scale` is 1, 2, 4 or 8, and
`displacement` is a constant. Any part may be omitted.

```asm
[rbx]                  ; the 8 bytes at rbx
[rbx + 8]              ; at rbx+8
[rbx + rcx*4]          ; at rbx + 4*rcx
[rbx + rcx*8 + 16]     ; at rbx + 8*rcx + 16
[rip + 0x2e4a]         ; relative to the next instruction — a global
```

The hardware computes this address in a single instruction. That is why the form
exists: indexing an array is one operation rather than a multiply followed by an
add.

For a reverse engineer, the `scale` field is free information. It is the size of
the elements of the array being indexed, and the compiler was obliged to emit it
correctly. A variable index multiplied by 4 means an array of 4-byte elements; by
8, an array of 8-byte elements or pointers. A *constant* displacement with no index
usually means a struct field rather than an array. Lecture 5 builds type recovery
on exactly this.

**RIP-relative addressing** deserves particular attention because it is the normal
way modern code refers to globals and constants. `[rip + 0x2e4a]` means "the
address of the next instruction, plus 0x2e4a". Position-independent code needs this:
the program does not know where it will be loaded, but it always knows the distance
from one part of itself to another.

The detail that catches everyone once: the offset is relative to the address of the
**next** instruction, not the current one. Compute from the wrong base and you land
somewhere plausible-looking and entirely wrong.

---

## 7. `lea` is arithmetic, not memory access

`lea` stands for *load effective address*. It computes the address an addressing
mode describes and puts that address in a register — **without accessing memory.**

```asm
lea rax, [rbx+8]    ; rax = rbx + 8          (compute)
mov rax, [rbx+8]    ; rax = the value at rbx+8 (go and fetch)
```

Because the addressing unit can multiply by 1, 2, 4 or 8 and add a constant in one
step, compilers use `lea` as a general-purpose calculator that also has the
advantage of not disturbing the flags:

```asm
lea rax, [rdi + rdi*2]      ; rax = rdi * 3
lea rax, [rdi*8 - 4]        ; rax = rdi * 8 - 4
lea rax, [rdi + rsi]        ; rax = rdi + rsi  (a three-operand add)
```

None of these touch memory and none of them are about addresses. When you see
`lea`, do not assume a pointer is involved. Read the brackets as an arithmetic
expression and decide from context whether the result is used as an address or as a
number.

---

## 8. Flags

The flags register records facts about the most recent arithmetic or logical
result. Four matter:

| Flag | Set when |
|---|---|
| **ZF** zero | the result was zero |
| **SF** sign | the result's top bit was set (negative, if signed) |
| **CF** carry | the operation carried/borrowed out of the top bit (unsigned overflow) |
| **OF** overflow | the result overflowed as a *signed* value |

`cmp a, b` computes `a - b` purely to set these flags and then throws the
subtraction away. If `a == b` the result is zero, so `ZF` is set. That is how
equality is tested: subtract and ask whether the answer was zero.

`test a, b` does the same with a bitwise AND.

Flags are consumed by conditional jumps, which is Lecture 3. For now the important
point is that the comparison and the branch are **two separate instructions**, and
that other instructions in between can overwrite the flags. When you are tracing,
the flags at the point of the jump are the ones set by the most recent
flag-modifying instruction — which is not always the `cmp` sitting immediately
above it.

---

## 9. Reading a function

Everything so far combines into reading real code. Consider:

```asm
sum_array:
    xor  eax, eax                  ; total = 0
    xor  ecx, ecx                  ; i = 0
.loop:
    cmp  ecx, esi                  ; compare i with n
    jge  .done                     ; if i >= n, finish
    add  eax, DWORD PTR [rdi+rcx*4]  ; total += arr[i]
    add  ecx, 1                    ; i++
    jmp  .loop
.done:
    ret                            ; return total in eax
```

Reading this with what we have:

- Two registers are zeroed at entry, so two things are being initialised. One of
  them accumulates, one of them counts.
- `[rdi + rcx*4]` — `rdi` is the base of an array of **4-byte** elements, indexed by
  `rcx`. Since `rdi` is the first argument and `rsi` the second (Lecture 4), this
  is a pointer and a count.
- The loop adds each element into `eax` and increments `rcx`.
- `eax` holds the result at `ret`, so the function returns a 4-byte integer.

The signature is effectively `int sum_array(int *arr, int n)`, recovered without
any symbol information, from the instruction widths and the addressing mode alone.

Note what did the work: the `*4` in the addressing mode, the 32-bit register names,
and the calling convention. None of that was written down by a programmer. All of
it was forced on the compiler by the machine.

---

## 10. `-O0` versus `-O2`

The same source compiled at different optimisation levels produces very
differently-shaped assembly, and you need to be fluent in both.

**At `-O0`**, every local variable has a stack slot. Reading a variable is a load
from `[rbp-N]`; writing it is a store. The assembly is verbose and maps almost
line-by-line onto the source. You can often read the source structure directly out
of the memory traffic.

**At `-O2`**, locals live in registers. The loads and stores largely disappear. The
`sum_array` example above is `-O2`-shaped: nothing touches the stack, and the loop
variable never has an address at all.

This is why `-O0` examples can be misleading as practice. Production binaries look
like the second kind. The course uses both deliberately: `-O0` to see the
correspondence to source, `-O2` because that is what you will actually meet.

---

## 11. Hand-execution, and why it is worth your time

The exercise that accompanies this material is to take twenty instructions and
compute the final register state by hand, on paper, before running them.

This is worth defending, because it is the point in the course where the effort
looks most obviously wasted — a debugger will do it instantly and correctly.

The reason to do it by hand is that the debugger tells you the answer and nothing
else. Tracing by hand is what builds the model that lets you *predict* the answer,
and prediction is what you need when you are reading code you cannot run: a
function deep in a stripped binary, a branch that only executes under conditions
you cannot yet reproduce, a fragment quoted in a report. Reading assembly fluently
means knowing what it will do without executing it.

There is a second reason, specific to this material. Almost everything in this
lecture is *arbitrary*: the zero-extension rule, which registers exist, the
encoding of addressing modes, the choice of `xor` to zero a register. None of it
follows from first principles; it is a set of conventions you either know or do
not. Arbitrary rules are exactly the material that cannot be reconstructed by
reasoning from general principles at the moment you need it.

This is also, concretely, where automated analysis is least reliable. Ask a model
to compute the final register state of a short instruction sequence and it will
usually track the arithmetic correctly and then report a 64-bit value where the
hardware would have zeroed the upper half — because the arithmetic is the part that
follows from general principles and the zero-extension rule is the part that does
not. The answer is confident, internally consistent, and wrong in one specific
place.

You catch that with `info registers`, and only if you knew the rule existed.

---

## Summary

- The machine state is sixteen registers, `rip`, the flags, and a flat byte array.
  There is nothing else.
- Memory has no types. Types are compiler fiction, discarded.
- Writing a 32-bit register zeroes the upper half; 16- and 8-bit writes do not.
- `movzx` versus `movsx` reveals whether the source value was signed.
- `[base + index*scale + disp]` — the `scale` is the array element size, free.
- RIP-relative offsets are measured from the **next** instruction.
- `lea` computes an address without accessing memory, and is mostly used as
  arithmetic.
- `cmp` and `test` set flags and discard their result. The comparison and the branch
  are separate instructions.
- Hand-execution builds prediction, which is what you need for code you cannot run —
  and this material is arbitrary, so it must be known rather than derived.

## Reading

- *Computer Systems: A Programmer's Perspective*, §3.1–3.5.
- *Reverse Engineering for Beginners* (Yurichev) — the reference to return to for
  "how does this construct compile?"
- Optional: microcorruption, tutorial and first two levels. A different instruction
  set on purpose — if the concepts transfer, you have learned the concepts.
