# Lecture 9 — Working like a reverse engineer: methodology on a real target

---

## 1. The skill is not reading code

Everything in the previous eight lectures was equipment. You can read instructions,
follow control flow, recover types, drive a debugger, and read a binary's structure.
None of that is yet reverse engineering, in the way a working reverse engineer means
it.

The reason is scale. A real binary has more code than you will ever read. `aurad` has
a few thousand instructions; a real device daemon or a browser has millions. You do
not read them. You read maybe two percent, and the entire craft is choosing *which*
two percent.

That choice cannot be delegated, and the reason it cannot is important: it depends on
your **goal**. "Where does it validate the licence" and "does it send my data
anywhere" and "why does it crash on this input" point at completely different two
percents of the same binary. No tool knows your goal. The triage is yours.

This lecture is the method that turns equipment into craft.

---

## 2. Triage: five steps before you read any code

The discipline is to spend the first few minutes deciding where to look, rather than
opening the disassembler at the entry point and scrolling. Amateurs scroll.
Professionals triage.

```
1. What is it?         file, readelf     — architecture, linkage, stripped?
2. What does it touch?  strace / ltrace   — files, network, environment
3. What can it say?     strings           — errors, formats, banners, paths
4. What does it call?   PLT list          — crypto? network? both?
5. Where is my target?  xref a relevant string or import → the code
   THEN read code — only the part triage pointed you at.
```

Worked on `aurad`, looking for command validation:

Step 3 gives, among the strings, `"bad command"`. Step 5: cross-reference it. It is
used in one function — the one that prints the error. That function is reached from
the command dispatcher. The dispatcher validates the command before dispatching. In
under a minute, from a string, you are looking at the exact function you wanted, in a
binary you have never opened, having read nothing irrelevant.

This is the Lecture 6 cross-reference technique elevated to a habit, and it is the
single most valuable thing in this lecture. The strings and the imports are a map,
and triage is reading the map before setting out rather than walking in a random
direction and hoping.

---

## 3. The hypothesis loop

Once you are looking at the right code, the work proceeds as a loop, and it is worth
making the loop explicit because it is the scientific method with a debugger
attached.

```
     ┌──────────▶  FORM a hypothesis  ──────────┐
     │            "this loop is a checksum"       │
     │                                            ▼
  RECORD it                                  PREDICT what you would
  (confirmed /                               observe if it were true
   killed /                                  "sum of the input bytes"
   still open)                                    │
     ▲                                            ▼
     └──────────────  TEST it  ◀──────────────────┘
              (feed a known input, read the value)
```

Four steps, and the one everyone skips is **record**.

Recording matters for three concrete reasons. You will not remember, two weeks from
now with no homework in between, what you concluded and why. Your work is not
reproducible if the steps exist only in your head — and a finding you cannot reproduce
is not a finding. And a dead end that is written down is a genuine result: it tells
you, and anyone after you, not to go there again. The reverse engineer's notebook,
with hypotheses dated and evidence linked and dead ends kept, is not bureaucracy. It
is what separates an investigation from thrashing.

The **predict** step is the one that does the intellectual work. Forming a vague
hypothesis is easy; committing in advance to what you would *see* if it were true is
what makes the test meaningful. "This is a checksum" is not testable. "This is a
checksum, so feeding four zero bytes should produce zero, and feeding one one-byte
should produce one" is testable, and running it either confirms or kills the idea in
seconds.

---

## 4. Knowing when to switch

Static and dynamic analysis each have a natural stopping point, and recognising it
saves hours.

Static reading is the right tool until you hit a value you cannot compute by
inspection: something derived from input, read from a file, or produced by a function
too tangled to follow by eye. At that point, stop reading and run it. Set a
breakpoint, feed a known input, and *read the value* instead of deriving it.

Dynamic analysis is the right tool until you need to understand a path that this
particular execution did not take, or until you have a concrete value and want to
know where in the code it came from. At that point, go back to reading, now armed
with the value.

The mistake in both directions is stubbornness: staring at an inlined transform
trying to compute it in your head when a breakpoint would hand you the answer, or
single-stepping through thousands of instructions when reading the function would
show you its shape at a glance. The two techniques are a pair, and fluency is knowing
which one the current question wants.

---

## 5. Recognising algorithm shapes

A large part of experienced triage is pattern recognition: knowing what common
algorithms look like so you can name them on sight rather than reversing them from
scratch. The key move is to **recognise, then look up** — you do not reconstruct AES
from first principles, you recognise its fingerprint and go read the specification.

Cryptography and encoding are recognisable by their constants:

| Algorithm | The tell |
|---|---|
| AES | the S-box, a 256-byte table beginning `63 7c 77 7b f2 6b 6f c5` |
| SHA-256 | initial hash values `6a09e667 bb67ae85 ...`; a 64-round loop |
| MD5 | the constant `67452301`; distinctive additive constants |
| base64 | the alphabet string `ABC...xyz0123456789+/`; shifts by 6, masks with `0x3f` |
| CRC32 | a 256-entry lookup table; one xor-and-shift per input byte |

Structural patterns are recognisable by shape rather than constants:

- **A state machine** is a `switch` on a state variable inside a loop, where the cases
  assign the next state. Protocol handlers and parsers are built this way.
- **A parser** has a cursor pointer that advances through a buffer and character-class
  checks — comparisons against `'0'` and `'9'`, against `'a'` and `'z'`.
- **A protocol handler** reads a length, then reads that many bytes. AURA-7's daemon
  does exactly this.

The point of the catalogue is not memorisation. It is to develop enough familiarity
that an unfamiliar function makes you think "that 256-byte table looks like a CRC
table" — at which point you look up CRC32 and confirm. Recognition narrows the search;
the reference supplies the detail.

---

## 6. The specialised zoo — recognise, do not memorise

Some things you will meet only occasionally, and the correct response to all of them
is the same: recognise the category, name it, look up the specific technique, and then
you are back to the fundamentals you already have. Nobody carries these in their head.

| You'll meet | It looks like | You do |
|---|---|---|
| **A packer** (UPX and friends) | a tiny `.text`, a huge high-entropy `.data`, a strange entry stub, no useful strings | recognise → unpack (often `upx -d`) → analyse the real thing underneath |
| **Anti-debugging** | a `ptrace(PTRACE_TRACEME)` call; timing checks; the program reading its own code for `0xCC` (Lecture 7) | recognise → patch the check or attach differently → read up on the specific trick |
| **A custom VM** | a fetch-decode-execute loop over a "bytecode" array; a big switch on an opcode byte | recognise → recover the opcode table → then it is ordinary RE of a small interpreter |
| **Obfuscation** | opaque predicates, bogus control flow, strings decrypted at runtime (Lecture 1's XOR) | recognise → often defeat it dynamically → read up |

This is the whole of what the course says about these. The learning objective is
explicitly *not* to be able to devirtualise a custom VM or defeat a commercial packer.
It is to recognise the smell, know the name to search for, and understand that looking
it up is the normal, professional thing to do — not a failure to have memorised it.

This is also, worth noting, exactly where an assistant is genuinely useful. "I think
this is a VM dispatch loop, help me recover the opcode semantics" is a task where you
supply the recognition and the judgement and the tool supplies the grind. That is the
partnership the whole course has been building toward: you decide what is worth doing
and whether the result is right; the machine does the volume.

---

## 7. Note-taking as a professional artifact

The output of a real reverse engineering effort is not "the answer". It is a document
that lets someone else — including you, later — understand and reproduce the finding.

For a licence algorithm, "the key is validated by a rolling hash" is not the
deliverable. The deliverable is: the address of the transform, the exact recurrence
it computes, the inputs you fed and the outputs you observed, the hypotheses you
tried and killed along the way, and enough detail that a reader could write the keygen
themselves from your notes. That is what a professional hands over, and it is why the
reverse engineer's notebook template exists and why this course keeps returning to it.

A finding you can state but not support is a guess. A finding documented with the
evidence that produced it is knowledge. The difference is the entire value of the
work.

---

## 8. Where the tool fails, on ground truth you built yourself

By this point in the course the failure modes are familiar, but this lecture provides
the strongest possible demonstration of the last one, because you will have
established the ground truth yourself, by hand, minutes earlier.

Hand a model the full decompilation of AURA-7's licence check and ask it for the exact
algorithm. It will produce something fluent and *mostly* right: "it computes a CRC32
of the key and compares against a stored value", or a rolling hash with a plausible
rotation and constant. The genre is correct. The structure is correct. It has
recognised the shape — the same recognition §5 is about.

And the specific constant, or the exact rotation, is wrong.

The check is decisive because you already did the real work: feed one known key
through the model's claimed algorithm and through the real binary, and compare the
accumulator after two bytes. They diverge. The model produced a plausible member of
the "licence hash" family — right family, wrong function — because it pattern-matched
to common implementations rather than tracing this specific one.

This is the whole course in a single observation. The model got you ninety percent of
the way there in one second: it correctly identified that this is a rolling hash, which
is genuinely useful and would have taken you longer. The last ten percent was a
rotation constant, and it was wrong, and it would have broken every key you generated,
and you caught it in ten seconds — *because you had recovered the real recurrence by
hand and could compare against it.* Someone without that ground truth would have
shipped the model's version and produced valid-looking, invalid keys.

You do not reject the tool. You do not trust it. You use it for the ninety percent,
and you are the ten percent, and the only thing that lets you be the ten percent is
that you can produce the ground truth the tool cannot.

---

## Summary

- The skill is not reading code; it is choosing which two percent to read. That choice
  depends on your goal, which is why it cannot be delegated.
- Triage in five steps — what is it, what does it touch, what can it say, what does it
  call, where is my target — before reading any code. Reach the target by
  cross-referencing a string or import.
- The hypothesis loop: form, predict, test, record. **Predict** does the intellectual
  work; **record** is what everyone skips and what makes the work reproducible.
- Switch between static and dynamic deliberately: read until you hit an uncomputable
  value, run to get it, read again with the value in hand.
- Recognise algorithm shapes by their constants (AES, SHA, CRC, base64) and their
  structure (state machine, parser, protocol handler). Recognise, then look up.
- The specialised zoo — packers, anti-debug, VMs, obfuscation — is recognise-and-look-
  up, never memorise. This is also where an assistant is most useful.
- The deliverable is a documented, reproducible finding, not an answer.
- On ground truth you built yourself, the tool's failure is stark: right algorithm
  family, wrong constant. You catch it only because you have the real recurrence to
  compare against.

## Reading

- *Practical Binary Analysis*, chapters 5–6.
- Read one published crackme write-up or malware teardown — for the *method*, how the
  author decided where to look and what to try, not for the specific target.
- Exercise: a full teardown of a difficulty-3 or -4 crackme, keeping a proper
  hypothesis log. The log matters more than the solution.
