# Infrastructure & Setup

Everything needed to deliver the course, and the one delivery risk that will
actually bite you.

---

## 1. The course image `re101`

One Docker image, everything pinned so optimiser output (and therefore the planted
AI-hostile properties) is reproducible.

```dockerfile
# re101 — reverse engineering course image
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    gcc g++ clang make \
    gdb \
    binutils file xxd bsdmainutils \
    strace ltrace \
    python3 python3-pip \
    gcc-aarch64-linux-gnu \
    gcc-mingw-w64 \
    upx-ucl \
    openjdk-21-jdk \
    radare2 \
    less vim nano git \
    && rm -rf /var/lib/apt/lists/*

# pwndbg
RUN git clone https://github.com/pwndbg/pwndbg /opt/pwndbg && \
    cd /opt/pwndbg && ./setup.sh

# pwntools
RUN pip3 install --break-system-packages pwntools

# Ghidra — pin a specific release; download separately and COPY in,
# or fetch a pinned version here. Verify the checksum.
COPY ghidra /opt/ghidra

# course binaries + solutions (mounted or baked per policy)
COPY re-course /opt/re-course

WORKDIR /work
```

**Pin the toolchain version explicitly** (`ubuntu:24.04` gives a fixed gcc, but
record the exact `gcc --version` in the image and in `BUILD-PLAN.md`). Every
AI-hostile property was verified against a specific compiler; a silent bump can
erase a planted trap. Re-run `make verify` in each session dir after any image
change.

**Verify on the image, not your laptop:** `set disassembly-flavor intel` works;
`ltrace` actually runs (it's flaky in containers — test it); Ghidra launches with
a writable project dir.

---

## 2. Two things that must be true before Session 1

- **Intel syntax by default.** Ship a `~/.gdbinit` in the image with
  `set disassembly-flavor intel`. The whole course uses Intel syntax; AT&T is
  noted once and never used.
- **ASLR disabled under gdb** is the default — but tell students bare execution
  still randomises, so their addresses won't match each other's. Pre-empts an hour
  of S7 confusion.

---

## 3. The one real risk: ARM Macs

A large fraction of the cohort will have Apple-silicon laptops. `docker run
--platform linux/amd64` works via emulation (Rosetta/qemu) but **degrades exactly
where the course lives**: single-stepping in gdb is slow, and pwndbg's register
diffing and some breakpoint behaviour can misbehave under emulation. This is worst
in **S2, S4, S7** — the sessions built on live stepping.

Static work (S1, S3 reading, S5, S6 Ghidra, S8 `readelf`) is fine emulated.
Dynamic single-stepping is the problem.

**Three mitigation tiers, in order of preference:**

### Tier 1 — a shared x86-64 box (most reliable, recommended)
A single Linux x86-64 machine (a cheap cloud VM or a lab server) with one SSH
account per student, the `re101` image or its packages installed. Everyone gets
identical, native, fast behaviour. **Set this up before Session 2** — it's the
session where emulation first bites, and discovering the problem live costs you a
third of the room.

- Cost: one modest VM for the cohort. Trivial next to the teaching time it saves.
- Bonus: you control the toolchain absolutely, so the AI-hostile builds are
  guaranteed identical for everyone.

### Tier 2 — emulated local container
Fine for the static-heavy sessions. Document the `--platform linux/amd64` incantation
and warn that stepping is slow. Acceptable as a fallback, not a primary plan for
S2/S4/S7.

### Tier 3 — Compiler Explorer for anything ISA-illustrative
Zero setup, instant, native. Used heavily in S1–S3 regardless of the above,
because the compile-and-compare loop is faster there than locally. Not a debugger,
so it doesn't cover the dynamic sessions — but it de-risks the "show me the asm"
half of the course completely.

**Recommended combination:** Tier 1 as the spine (SSH box for all dynamic work),
Compiler Explorer for the static/illustrative parts, Tier 2 as the "my SSH is
down" fallback. Do **not** rely on Tier 2 alone for S2/S4/S7.

---

## 4. Failure fallbacks (so a bad day never costs a session)

- **Every live demo is pre-recorded as an asciinema cast** (`sNN-demoM.cast`,
  referenced in each session's prep checklist). Projector dies, image breaks, SSH
  box down — play the cast and narrate. The session survives.
- **Ghidra will fail to launch on someone's machine.** Guaranteed, every offering.
  Have `s06-demo1.cast` ready and a shared-box Ghidra. Pair the affected student
  up; don't debug one JDK in front of thirty people.
- **A binary "doesn't reproduce the trap."** Run `make verify` in that session's
  dir; it tells you which property broke. Rebuild from the pinned toolchain.

---

## 5. Solutions repository

Publish after each session. **Include the reasoning, not just the answer** — the
reasoning is what's being taught. A solutions repo that lists flags teaches
students the flag was the point. Structure:

```
solutions/
  sNN/
    README.md          # the method, narrated: how you'd actually get here
    answers.md         # the concrete answers
    scripts/           # e.g. logtransform.py, mkconfig.py, keygen.py
    cast/              # the demo recordings
```

---

## 6. Pre-flight checklist (once, before the course; and the per-session ones live
in each session doc)

- [ ] `re101` image built, `gcc --version` recorded, `make verify` green in all
      session dirs
- [ ] Tier-1 SSH box provisioned, one account per student, tested from an ARM Mac
- [ ] Every Falsification Drill run against a *current* model; failure modes
      confirmed and scoreboard exemplars updated (see BUILD-PLAN §verification)
- [ ] All five reference cards printed, class set
- [ ] AI Scoreboard poster printed, blank, columns drawn
- [ ] asciinema casts recorded for every demo
- [ ] Ghidra pinned version, checksum verified, launch-tested on the image
