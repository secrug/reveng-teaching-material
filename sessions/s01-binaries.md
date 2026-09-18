# Session 1 — Binaries, and why RE is inference

**The one idea:** compilation destroys information. What you get back is a
*reconstruction*, not a recovery — which is why reverse engineering is a skill
and not a button.

---

## Outcomes

By the end, every student can:

1. Identify an unknown file from its header bytes and structure alone.
2. Explain what `-O0` → `-O2` destroys, with a concrete example they produced.
3. State why two different C programs can produce byte-identical machine code,
   and what that implies for RE.
4. Use `file`, `strings`, `xxd`, `nm`, `readelf -h` with intent.
5. Name one thing an LLM confidently got wrong about a binary, and the evidence
   that proved it wrong.

---

## Prep checklist

- [ ] `s01/` binary pack distributed (8 mystery files + `crackme01`, `crackme01x`)
- [ ] Docker image tested on at least one student laptop of each type
- [ ] Compiler Explorer open in a tab, C and asm panes side by side, `-O0`
- [ ] Reference card **#1 (Toolbox)** printed, one per student
- [ ] Reference card **#2 (x86-64)** printed — issue at the *end*, for S2
- [ ] AI Scoreboard poster on the wall, columns drawn, empty
- [ ] Terminal font ≥ 18pt. Check from the back row. Actually walk to the back row.
- [ ] Fallback asciinema casts loaded: `s01-demo1.cast`, `s01-demo2.cast`

---

## 0:00 — Opening (this session only: 10 min, warm-up replaced)

There is nothing to retrieve yet, so this slot is the course frame. Ten minutes,
not more.

**Slide 1, and the only text-only slide in the course:**

> AI moved the bottleneck from *"can you read assembly"* to *"do you know what to
> ask, and can you tell when the answer is wrong."* Both are fundamentals.

Say, roughly:

> "Some of you will try an LLM on today's exercise. It'll probably work. I want
> you to do that — openly, not under the desk. What this course is about is the
> second half of that sentence. Anyone can get an answer now. The job is knowing
> whether it's true."

Then the deal on the decompiler, stated plainly:

> "There's a tool called a decompiler that turns machine code back into
> C-looking code. It's very good. You're not getting it until Session 6.
>
> Not to be cruel — because the decompiler is the previous generation's version
> of exactly the thing we're talking about. It produces fluent, plausible,
> confident output, and it is sometimes wrong, and you cannot tell which unless
> you can read the assembly underneath. Same problem, older tool. You'll get it
> in Session 6 and your first job with it will be to catch it lying."

Housekeeping: biweekly, three hours, nothing graded, everything optional, the
room is for working not for listening. Then the boundary, in one sentence: **we
reverse the binaries this course gives you, not other people's** — full treatment
in S10.

---

## 0:10 — Cold open (15 min)

On screen: `crackme01`. Run it.

```
$ ./crackme01
password: hunter2
nope.
```

**The question on the board:** *What is the password, and how do you know?*

Students write a prediction — the password if they think they have it, otherwise
**the method they'd use**. Two minutes, pen on paper, no laptops open. Say
explicitly: "a method is a valid answer; 'I don't know' is not."

Then let them loose with laptops for five minutes. Someone will run `strings` and
get it. Someone else will paste the binary into a model and get it. Both are
fine. Both are *supposed* to happen.

Collect answers on the board. Then:

> "Right. Everybody got it. Hold that feeling."

Hand out `crackme01x`. Same program. One difference.

```
$ strings crackme01x | grep -i pass
password:
```

The password is gone. Nothing else changed.

> "Same program. The string is XOR'd with a constant at startup. Your technique
> just died, and so did the model's, because the model was reading the same
> strings you were. It didn't *understand* the program. Neither did you. That's
> not an insult — it's the entire syllabus."

**Do not solve `crackme01x` now.** It is the cold-open reveal at 2:55, and it
stays visible on a side screen all session as a standing provocation.

---

## 0:25 — Teach A: from source to bytes (35 min)

Terminal and Compiler Explorer, not slides.

### A1 — The pipeline (10 min)

Draw on the board as you go, left to right, and leave it up all session:

```
  hello.c  ──cpp──▶  hello.i  ──cc1──▶  hello.s  ──as──▶  hello.o  ──ld──▶  hello
  source            preprocessed        assembly         object           executable
                                                         (relocatable)    (linked)
```

Do it live:

```bash
gcc -E hello.c -o hello.i      # 800 lines from 5. Scroll it. Let them react.
gcc -S hello.c -o hello.s      # now it's assembly
gcc -c hello.s -o hello.o      # now it's bytes
gcc hello.o -o hello           # now it runs
```

At each arrow ask: **what did we just lose?**

- After `cpp`: comments, macro names, `#include` structure.
- After `cc1`: variable names (mostly), types, expression structure, your
  formatting, your intent.
- After `as`: mnemonics — it is now bytes.
- After `ld`: file boundaries; and with `-s`, the symbol names too.

> "Every arrow is one-way. You're going to spend this course walking backwards up
> them, and at every step you are *guessing*, using evidence. Good guesses. But
> guesses."

### A2 — Many-to-one (12 min)

The core idea of the session. Compiler Explorer, `-O1`:

```c
int f(int n) { int s = 0; for (int i = 1; i <= n; i++) s += i; return s; }
int g(int n) { return n * (n + 1) / 2; }
```

Show that at `-O2` these can produce the *same* machine code.

Ask: **given only the assembly, was the source `f` or `g`?**

Let them sit in it. Then say it:

> "There is no answer. The information is *gone*. Not hidden — gone. This is why
> nobody will ever ship a perfect decompiler, and why no model will ever be
> perfect at this either. It's not a technology problem. It's an information
> problem."

Immediately follow with the consequence, so it doesn't land as despair:

> "So what *is* the job? You're not recovering the source. You're building a
> model of the behaviour that's good enough for your purpose. 'Good enough for
> your purpose' is a judgement call. Judgement is what you're here for."

### A3 — What survives, and the toolbox (13 min)

What survives compilation, reliably:

| Survives | Why it's useful |
|---|---|
| Control flow structure | Loops and branches are still loops and branches |
| String and numeric literals | `.rodata` is a goldmine, and a trap (see 0:10) |
| Library calls | Dynamic symbols must be named to be linked |
| Data layout and offsets | The machine needs exact addresses |
| Syscalls | The kernel boundary is fixed |
| Algorithmic *shape* | Crypto constants, table sizes, loop counts |

Live, on the mystery-file pack — this is the toolbox for Lab A:

```bash
file mystery1                 # heuristic guess from magic bytes
xxd mystery1 | head -4        # the ground truth: look at the bytes yourself
strings -n 8 mystery1 | head  # printable runs
nm -C mystery1                # symbols, if any survived
readelf -h mystery1           # ELF header, if it is one
```

Emphasise, because it recurs all course: **`file` is a guess. `xxd` is a fact.**
Demonstrate by renaming a PNG to `.exe` — `file` is unmoved, and that's the point:
it reads content, not names. Then corrupt one magic byte and watch `file` fall
back to "data" while the file is still 99.99% a PNG. Tools have models of the
world. The models are wrong sometimes. Look at the bytes.

---

## 1:00 — Break (10)

---

## 1:10 — Lab A: Eight mystery files (40 min)

Full spec: [`labs/s01-lab.md`](../labs/s01-lab.md). Summary:

- **Core** — identify all 8 files, stating for each *which evidence* decided it.
- **Stretch** — compile one C file at `-O0`, `-O2`, `-Os`, diff the assembly, and
  write down exactly what was destroyed at each level.
- **Boss** — two of the eight are the *same* program, different builds. Find the
  pair and prove it. (Explain-back required.)

**Circulate.** The intervention that matters most today: students who answer
"`file` said so." Push back every time — *"and if `file` is wrong?"* The habit
of reaching for `xxd` to confirm is the single most transferable thing in this
session.

---

## 1:50 — Teach B: live demo, with the wrong turns kept in (25 min)

**Target:** `aura-fw.bin`. First contact with AURA-7.

Frame it:

> "This is the firmware blob from a device called AURA-7. It's made up — but it's
> made up the way real ones are. We'll be taking this thing apart for the next
> five months. Today we just want to know what it *is*."

Work it live. **The wrong turns are scripted — do them:**

1. `file aura-fw.bin` → "data". Useless. Say so. *(Wrong turn 1: hoping a tool
   will do your thinking.)*
2. `strings` → a version banner, a copyright line, `/dev/ttyS0`, and the word
   `AURA`. Build a hypothesis out loud: embedded device, serial port, has a
   version.
3. `xxd | head` → a magic number `41 55 52 41` — "AURA" in ASCII. **Now go to the
   board and decode those four bytes by hand, live.** This is the first time they
   see bytes-to-meaning done manually, and it should look easy, because it is.
4. Announce the next 4 bytes are a version field. Read them. Get it backwards.
   Pause. *(Wrong turn 2 — the important one.)* "That says version 65536, which
   is stupid. So I've got something wrong." Work out endianness at the board.
   Re-read. Version 1.2.
   > "That'll happen to you constantly. The tell is that the answer was *absurd*.
   > Absurd is a gift — it means you've found the bug. The dangerous errors are
   > the plausible ones."
5. Find a length field. Check it against `ls -l`. It doesn't match. *(Wrong turn
   3.)* Consider: header not counted? Compressed? A checksum after the data? Say
   "I don't know yet — writing it down as an open question," and physically write
   it on the board under **OPEN QUESTIONS**.

That board section stays up all course. It is the visible artifact of the
single most important professional habit: unresolved things get *recorded*, not
suppressed.

End with the shape they built in twenty-five minutes without any tool more
advanced than `xxd`:

```
offset 0x00  "AURA"        magic
offset 0x04  01 02         version 1.2  (little-endian, 2 x u16)
offset 0x08  ????          length-ish, doesn't match file size — OPEN
offset 0x10  ...           sections?
```

---

## 2:15 — Break (10)

---

## 2:25 — Lab B: AURA-7 first contact (30 min)

Students repeat the demo method on `auractl` and `aurad`, and produce a one-page
**triage note** for each: what kind of file, dynamically or statically linked,
stripped or not, what libraries, what strings suggest, and — required — **three
open questions**.

The open questions are the graded part, if anything here were graded. Push for
specific ones. "How does it work?" is not a question; "what produces the 16-byte
value printed on a failed licence check?" is.

Seed the drill during this block: **"before you finish, ask a model what
`auractl` does and keep its answer."**

---

## 2:55 — Falsification Drill + close (5 min)

**The claim.** Take a student's model output. It will contain something like:
*"`auractl` validates the licence key by comparing it against a hardcoded string
in `.rodata`."*

**Run the script:**

1. *State it.* Written on the board, one sentence.
2. *What would falsify it?* — If the comparison were against a hardcoded string,
   that string would be in `strings` output, and there would be a `strcmp`-shaped
   call. Get this from the room, not from yourself.
3. *Observe.* `strings auractl | grep -c .` — no candidate. `nm -D auractl` — no
   `strcmp`, but there **is** `memcmp`, against something computed.
4. *Verdict.* **Wrong, plausibly.** The reason: the model pattern-matched "licence
   check" to the most common tutorial implementation. It was not reading; it was
   predicting. Write that in the reason column.

Then the reveal. Back to `crackme01x`:

> "Two hours ago this was unsolvable because `strings` didn't work. Here's what
> you'll be able to do by Session 3."

Show it for thirty seconds, no explanation — `objdump -d`, scroll to the XOR loop,
point at it.

> "That loop. It undoes the obfuscation for you, because the program has to be
> able to read its own password. The program always tells you. You just have to
> be able to read it. That's the course."

Point at the optional track (one reading, one exercise, one crackme — all
optional, all on the wiki) and hand out reference card #2 for next time.

---

## Scoreboard entry

| S | Claim | Verdict | Reason |
|---|---|---|---|
| 1 | `auractl` compares the licence to a hardcoded `.rodata` string | ✗ Wrong | Pattern-matched to the common tutorial shape; no such string exists; the real path uses `memcmp` on a computed value |

---

## Lecturer notes — where this session goes wrong

**Students find `crackme01x` too discouraging.** Watch for it. The fix is the
last five minutes — they must leave having *seen* the solution exists and is
readable. Do not skip the reveal to save time.

**The many-to-one demo falls flat if the compiler doesn't cooperate.** Optimiser
behaviour varies by version. **Verify the exact `f`/`g` codegen on your image
before the session.** If they don't converge, the fallback pair is in
`binaries/BUILD-PLAN.md` §S1.

**Someone asks "so why not just always use AI?" in the first hour.** Good — this
is the best possible question and you want it early. Answer honestly: "For a lot
of tasks, you should, and I'll show you which ones in Session 6 and Session 10.
Today's answer is just: you saw it fail an hour ago, and you couldn't tell until
you checked. The whole course is about being the person who can check." Then move
on. Do not litigate it for ten minutes; the demonstrations do the work over five
months, not one argument in week one.

**Running long.** Cut Lab A Boss tier, then A3's PNG-corruption bit. Protect
the cold-open reveal above everything else in this session.

---

## Optional track → [RESOURCES.md](../RESOURCES.md#session-1)

- **Read:** CS:APP ch. 1 (20 min) — the pipeline, properly.
- **Do:** compile something of your own three ways and diff it.
- **Crackme:** crackmes.one, difficulty 1, any "strings" tier challenge.
- **Self-check:** 5 questions, answers included.
