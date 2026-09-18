# Lab 7 — Break, watch, understand

**Time:** Lab A 40 min + Lab B 30 min · **Pack:** `s07/licensed`, `patchme`;
reference card #4

---

## Lab A

### Core — Understand the check (not defeat it)

Break on the comparison in `licensed`, read **both** operands, and report what it
compares your input against. The deliverable is *understanding*, not "make it say
valid."

```bash
gdb ./licensed
(gdb) b <cmp address>        # find it via objdump first
(gdb) run
(gdb) info registers        # read both operands
```

**Deliverable:** what is compared to what, and where the "expected" value came
from.

### Stretch — Watch the value

Set a watchpoint on the variable holding the parsed/derived key. Report every
place it's written and by what code.

```bash
(gdb) watch <addr or expr>
(gdb) run                    # stops on each write
```

**Deliverable:** the write history of that value — the data-flow into the check.

### Boss — Keygen, no patching (explain-back)

Make `licensed` accept a key by **understanding the transform and hand-computing a
valid key** — patching forbidden. *Then*, separately, achieve the same by
patching, and write one paragraph on why the patch is the inferior solution here.

**Deliverable:** a valid key (computed, not patched) + the patch + the paragraph.
Explain the transform to a neighbour, notes closed.

#### Solution outline

`licensed`'s check is a small reversible transform (e.g. a checksum over the key
that must equal a constant, or a per-char transform compared to a table). The
keygen requires understanding it; the patch requires only flipping the `je`. The
paragraph should note: the patch is input-specific and brittle, teaches nothing
about valid keys, and breaks if there's a second check. This is the "patch vs
understand" thesis, self-discovered.

---

## Lab B — Script the observation

Write a **gdb Python script** that logs every call to AURA-7's transform function
with its input byte and the running accumulator.

- **Core:** breakpoint script printing the accumulator each iteration.
- **Stretch:** log `(input byte, accumulator)` as a table; identify the per-round
  operation.

```python
# skeleton (full version in solutions repo)
import gdb
class Log(gdb.Breakpoint):
    def stop(self):
        acc = int(gdb.parse_and_eval("$<reg or var>"))
        print(f"acc={acc:#x}")
        return False        # don't halt, just log
Log("*<transform addr>")
gdb.execute("run")
```

#### Solution outline

The correct sample point is *after* the round updates the accumulator, and the
accumulator lives in a specific register/local — getting that wrong is exactly the
subtle error the drill exploits when the model writes this script. Provide a
correct `logtransform.py` in the solutions repo.

---

## TA notes

Channel the patching euphoria into the Boss tier's no-patch rule. The message all
lab: a patch is a great *experiment* and a poor *understanding*. A student who can
only patch has not reversed the check — they've disabled it.
