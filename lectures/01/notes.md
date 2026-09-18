# Lecture 1 — Binaries, and why reverse engineering is inference

---

## 1. What reverse engineering is

A compiler takes source code and produces machine code. Reverse engineering is the
attempt to go the other way: to start from machine code and recover an
understanding of what a program does and how it does it.

The word "understanding" is doing a lot of work in that sentence. We are not
recovering the source code. In most cases the source code is not recoverable, and
not because it is hidden or encrypted — because it no longer exists anywhere in
the file. Compilation is a lossy process. It discards information permanently, in
the same way that converting a photograph to greyscale discards colour. You can
make an educated guess at what colour a grey pixel used to be, but you are
guessing, and no amount of cleverness turns the guess back into a measurement.

This makes reverse engineering a form of **inference**: reasoning from evidence to
the most plausible explanation, under uncertainty. It is closer to reading an
X-ray than to decrypting a message. A decrypted message is either right or wrong.
An X-ray is interpreted, and the quality of the interpretation depends on how much
the radiologist knows about anatomy.

That comparison sets the standard for this course. The evidence in front of you is
always complete — every byte of the program is there, and nothing is hidden from
you. What varies is how much of it you can read. Everything we do from here is
about building the anatomy knowledge that turns those bytes into an explanation.

---

## 2. The compilation pipeline

Compilation is usually described as one step, `gcc hello.c -o hello`, but it is
four, and each one is a separate transformation with its own losses.

```
  hello.c  ──cpp──▶  hello.i  ──cc1──▶  hello.s  ──as──▶  hello.o  ──ld──▶  hello
  source            preprocessed        assembly         object           executable
                                                         (relocatable)     (linked)
```

**The preprocessor (`cpp`)** expands `#include` directives, substitutes macros,
and strips comments. It is a text-to-text transformation. A five-line `hello.c`
typically becomes eight hundred lines of `hello.i`, almost all of it the contents
of `stdio.h`.

```bash
gcc -E hello.c -o hello.i
```

**The compiler proper (`cc1`)** turns preprocessed C into assembly language for a
specific target architecture. This is where nearly all the information loss
happens, and we will spend the rest of this lecture on it.

```bash
gcc -S hello.c -o hello.s
```

**The assembler (`as`)** turns assembly text into machine code — actual bytes —
packaged in an object file. The mapping from assembly mnemonics to bytes is
essentially one-to-one and mechanical.

```bash
gcc -c hello.s -o hello.o
```

**The linker (`ld`)** combines object files and libraries into a single executable,
resolving references between them and assigning final addresses.

```bash
gcc hello.o -o hello
```

Every arrow in that diagram runs one way. Reverse engineering is the work of
walking back up them, and at every step you are reconstructing something that was
thrown away rather than looking something up.

---

## 3. What each stage destroys

It is worth being specific about what is lost, because the losses are what you
will spend the rest of the course compensating for.

**The preprocessor destroys** comments, macro names, and the structure of your
includes. A binary never contains the comment explaining why a constant is 0x1F.
It does not contain the name `MAX_RETRIES` — only the number 5 that the macro
expanded to.

**The compiler destroys** the most, and this is the important one:

- **Variable names.** `customer_balance` becomes an offset from a register, such
  as `[rbp-0x18]`. The name is gone entirely.
- **Types.** The machine has no concept of `int`, `float`, `char *` or `struct
  account`. It has registers, addresses, and operations of various widths. A type
  is a fiction the compiler maintained during compilation and then discarded.
- **Expression structure.** `(a + b) * c` and an equivalent sequence of temporary
  assignments produce identical machine code.
- **Function boundaries, sometimes.** A small function may be inlined into its
  caller and cease to exist as a separate entity.
- **Control structure.** A `for` loop, a `while` loop, and a `goto`-based loop can
  all compile to the same sequence of compares and jumps.

**The assembler destroys** essentially nothing of interest. Assembly and machine
code are two notations for the same thing, which is why disassembly is largely
reliable and decompilation is not.

**The linker destroys** the boundaries between source files, and — if the binary is
*stripped* — the symbol table that records function names.

---

## 4. Compilation is many-to-one

This is the central idea of the lecture, and the reason reverse engineering has
the character it does.

Consider two functions that compute the same thing by different means:

```c
int f(int n) {
    int s = 0;
    for (int i = 1; i <= n; i++)
        s += i;
    return s;
}

int g(int n) {
    return n * (n + 1) / 2;
}
```

At `-O0` these compile to obviously different code: `f` contains a loop, `g`
contains a multiply and a shift. But turn on optimisation, and the compiler
recognises that `f`'s loop computes a closed-form sum and replaces it with exactly
the arithmetic that `g` performs. At `-O2` the two functions can compile to
**byte-identical machine code.**

Now ask the reverse engineer's question. Given only that machine code, was the
original source `f` or `g`?

There is no answer. It is not that the answer is difficult to find, or that we
lack a sufficiently clever tool. **The information that distinguished them no
longer exists.** Two different inputs produced the same output, and no function can
invert a many-to-one mapping.

This has three consequences worth stating plainly.

First, **a perfect decompiler is impossible.** Not impractical — impossible, for
information-theoretic reasons, in the same way you cannot recover a deleted file
from an empty disk. Any tool that claims to recover source is producing a
*plausible* source, not *the* source.

Second, **the same limit applies to any tool at all**, including one that has read
every program ever written. Better priors let you guess better. They do not
recreate destroyed information.

Third, and most usefully: **the goal is not to recover the source.** The goal is to
build a model of the program's behaviour that is good enough for whatever you are
trying to do. If you want to know whether a program sends your data to a server,
you do not need its variable names. "Good enough for the purpose" is a judgement
call, and judgement is the skill this course develops.

---

## 5. What survives

The picture so far is bleak, so here is the other half of it. Compilation destroys
a great deal, but it cannot destroy anything the machine needs in order to run.
That constraint is your leverage, and it is worth internalising as a general
principle: **look for what the compiler had no choice about.**

| Survives | Why, and why it helps |
|---|---|
| Control flow structure | The program must still branch and loop the way it did. Loops remain loops. |
| String and numeric literals | They must be present in memory for the program to use them. |
| Library and system calls | To call `printf`, the binary must name `printf` so the linker can find it. |
| Data layout and offsets | The machine needs exact addresses; field offsets are literal in the code. |
| Syscalls | The boundary to the kernel is fixed and numbered. |
| Algorithmic shape | An AES implementation still contains the AES constants. A loop over 256 entries is still 256 iterations. |

Almost every technique in this course is an application of that principle. Argument
registers reveal function signatures because the calling convention is not
optional. Address scaling reveals array element sizes because the machine must
compute the right address. Padding reveals struct layout because the hardware
requires alignment.

---

## 6. Identifying a file

Before you can analyse a file you need to know what it is. Files announce their
type through **magic numbers** — fixed byte sequences at a known offset, almost
always the very beginning.

| Bytes | Format |
|---|---|
| `7f 45 4c 46` | ELF (Linux executables, objects, shared libraries) |
| `4d 5a` | PE / MZ (Windows executables) |
| `89 50 4e 47` | PNG |
| `1f 8b` | gzip |
| `ca fe ba be` | Java class file, or Mach-O fat binary |

`7f 45 4c 46` is `0x7F` followed by the ASCII characters `E`, `L`, `F` — a
deliberate design: one non-printable byte so the file is not mistaken for text,
then a human-readable tag.

The `file` command identifies files by checking these signatures against a
database of rules. It is fast and usually right, and it is important to understand
exactly what it is doing, because it is a *heuristic*. `file` does not look at the
filename and it does not verify the whole file. It matches patterns.

This produces two failure modes you will meet immediately. A file whose magic bytes
are damaged is reported as `data` even when the rest of it is a perfectly
well-formed PNG. And a file can be deliberately constructed to match the signature
of a format it is not.

The habit to build from this lecture onwards: **`file` gives you a hypothesis,
`xxd` gives you evidence.** Confirm the guess against the bytes. It costs three
seconds and it will save you hours.

---

## 7. The triage toolbox

These are the commands to run on first contact with an unknown binary, before any
disassembly.

```bash
file X            # what is it?  (a hypothesis — confirm it)
xxd X | head      # the actual bytes: magic number, structure
strings -n 8 X    # printable runs: error messages, formats, paths, banners
nm -C X           # symbol names, if the binary is not stripped
readelf -h X      # ELF header: architecture, type, entry point
readelf -d X      # dynamic section: which libraries it needs
readelf -S X      # sections: .text, .rodata, .data, ...
```

Two of these deserve comment now.

`strings` scans a file for runs of printable characters and prints them. It is
crude and it is often the single most productive thirty seconds you will spend on
a binary, because programs are full of text they must carry in order to function:
error messages, format strings, file paths, URLs, version banners, SQL, help text.

`readelf -h` tells you the architecture (so you know what instruction set you are
about to read), whether the file is an executable, a shared object, or a
relocatable object, and the entry point address.

---

## 8. Strings: the first technique, and its limit

Consider a program that asks for a password and rejects the wrong one.

```
$ ./crackme01
password: hunter2
nope.
```

Run `strings` on it and the password is likely to be sitting there in plain text,
because the program has to compare your input against something, and the simplest
implementation stores that something as a string literal. The literal lives in the
`.rodata` section, and `strings` reads it straight out.

This works often enough to be worth always trying, and it is the reason `strings`
is step three of triage.

Now consider a second version of the same program in which the expected password
is stored XOR-encoded and decoded at startup:

```c
static char secret[] = { 0x2a, 0x31, 0x2e, 0x2b, ... };  /* each byte ^ 0x5A */

for (int i = 0; i < len; i++)
    secret[i] ^= 0x5A;
```

`strings` now finds nothing. The bytes in the file are not printable characters,
so they are not printed. The technique has failed completely, and it has failed
without any warning — an empty result looks exactly like "there was nothing to
find."

The important observation is not that the obfuscation is clever. It is trivial. It
is that the technique which worked a moment ago tells you nothing about *why* it
worked, and so it gives you nothing to fall back on when it stops working.

And the program still knows the password. It must — it compares your input against
it successfully. The decoding loop is right there in the code, doing the work for
you. Recovering the password means reading that loop, which requires everything
lectures 2 and 3 are about.

**The program always tells you. The only question is whether you can read it.**

---

## 9. Optimisation levels

The compiler's optimisation level dramatically changes how readable the output is,
and you should know what to expect from each.

**`-O0`** performs almost no optimisation. Every variable gets a stack slot, and
every access to it is an explicit load and store. The assembly maps closely to the
source: you can usually see the statements in order. This is the friendliest code
to read and, unfortunately, is not what real software ships as.

**`-O2`** is the common production setting. Variables live in registers rather than
memory, so the loads and stores mostly vanish. Small functions are inlined into
their callers and disappear as separate entities. Loops may be unrolled, rewritten,
or replaced with closed-form arithmetic. Dead code is removed. Computations are
reordered.

**`-Os`** optimises for size rather than speed: less inlining and unrolling, and a
preference for shorter instruction encodings.

The practical consequence is that the same source produces very different-looking
binaries, and a technique that works on `-O0` teaching examples may not transfer
directly to `-O2` production code. This is why the course uses both.

A useful exercise, and one you should do yourself at least once: compile something
you wrote at all three levels and diff the assembly. Seeing your own loop turn into
three instructions is more convincing than being told it happens.

---

## 10. First contact: a worked example

Everything above applies to a concrete artifact. `aura-fw.bin` is a firmware image
from a device called AURA-7, and we will be taking it apart across the whole
course. It is synthetic — not a real product — but it is built the way real ones
are.

Running `file` on it gives `data`. That is the correct answer and a useless one: it
means no signature in the database matched. Firmware images generally have no
standard format, because the only software that needs to read them is the
bootloader that ships with the device.

`strings` is more productive. It yields a version banner, a copyright line, the
path `/dev/ttyS0`, and the word `AURA`. From four pieces of text we can already
form a hypothesis: an embedded device that talks over a serial port and has a
version number.

Then look at the bytes directly.

```
00000000: 4155 5241 0100 0200 0020 0000 ...   AURA.... ...
```

The first four bytes are `41 55 52 41` — `AURA` in ASCII. This is a magic number;
it is simply not one that `file` knows about. The device's own bootloader checks
those four bytes to confirm it has been handed a valid image, exactly as the
kernel checks `7f 45 4c 46`.

The next bytes are the version. Here we have to be careful, and this is the first
appearance of a problem that will recur constantly.

---

## 11. Endianness

The bytes at offset 4 are `01 00 02 00`. What version is that?

x86 is **little-endian**: multi-byte integers are stored least-significant byte
first. So the two-byte value at offset 4 is not `0x0100` but `0x0001` — the value
1. The two-byte value at offset 6 is likewise 2. Version 1.2.

Read them in the wrong order and you get version 256.512, which is absurd. That
absurdity is useful. Byte-order errors usually produce results that are obviously
wrong: enormous numbers, negative lengths, timestamps in the year 30,000. When an
extracted value is ridiculous, byte order is the first thing to check.

Strings are unaffected, which is why `AURA` reads correctly in the dump. A string
is an array of single bytes, not a multi-byte integer, so there is no byte order to
get wrong. This is why text in hex dumps reads left to right while numbers appear
reversed — a detail that confuses people for longer than it should.

The general lesson is worth extracting: **an implausible result is a gift.** It
tells you immediately that you have made an error. The errors that cost you a day
are the ones that produce plausible values — a length that is merely wrong rather
than impossible, a version number that could be real. Those you catch by checking
against something independent, not by noticing they look odd.

Continuing the header, there is a length field at offset 8. Compared against the
actual file size it does not match — the file is larger than the length claims.
Several explanations are possible: the length might exclude the header, the data
might be compressed, or there may be a checksum or signature appended after the
payload.

We do not have enough information to decide yet, and the correct action is to write
the question down and continue. An unresolved question that has been *recorded* is
a normal state of work. An unresolved question that has been silently forgotten is
how you end up with a wrong model of the program. This particular question stays
open for most of the course and is answered in Lecture 9.

---

## 12. Why this matters now that machines can read assembly

A language model will solve a `strings`-based crackme instantly. It will read
assembly faster than you can and produce a fluent explanation of what a function
does. Given how much of this lecture is about techniques a machine can perform,
the obvious question is why learn them.

The answer follows directly from section 4. Compilation destroys information, so
recovering intent is inference, not lookup. A tool that produces the *most likely*
explanation is genuinely useful, and it is wrong specifically where the program
departs from what is likely — which is precisely where the interesting programs
depart from it. Obfuscated code, unusual constructs, deliberate misdirection, and
custom algorithms are all, by construction, unlikely.

This produces a failure mode with a particular shape. Wrong output does not arrive
labelled as wrong. It arrives with the same fluency and confidence as correct
output. A model shown only the `strings` output of a stripped binary will
frequently narrate a detailed account of the program's behaviour built from a
handful of format strings — an account that is coherent, specific, plausible, and
substantially invented.

Detecting that requires knowing what the evidence actually supports. There is a
concrete standard for this, and it is the method for the rest of the course: for
any claim about a binary, ask **what observation would show this to be false**,
and then make that observation. A claim about a string is checked against the
bytes. A claim about a comparison is checked against the disassembly. A claim about
behaviour is checked in a debugger.

Note that this is not a special procedure for handling machine output. It is the
ordinary discipline of the field, and it applies identically to your own
hypotheses, which will also be confident and also sometimes wrong. The tool has not
changed what the work is. It has made the ability to verify the scarce part.

---

## Summary

- Reverse engineering is inference from evidence, not recovery of source.
- Compilation is a one-way, many-to-one transformation. The information that
  distinguished two different sources with the same behaviour is genuinely gone.
- What survives is whatever the machine needs to run: control flow, literals,
  library calls, data layout, algorithmic shape. That is your leverage.
- `file` is a hypothesis; `xxd` is evidence. Confirm.
- `strings` is the highest-value first move and tells you nothing about why it
  worked, so it strands you when it fails.
- x86 is little-endian. Implausible extracted values usually mean byte order.
- Record open questions rather than forgetting them.
- Any claim about a binary — yours or a machine's — is checked by naming the
  observation that would falsify it and making that observation.

## Reading

- *Computer Systems: A Programmer's Perspective*, chapter 1 — the compilation
  pipeline in full.
- *Reverse Engineering for Beginners* (Yurichev), opening chapters — free, and the
  reference to return to for "how does this construct compile?"
