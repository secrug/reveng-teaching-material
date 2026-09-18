# AURA-7 CTF Suite

Original CTF challenges for the team to train on and to field in external
competitions, hosted on **CTFd**. Designed to be **resistant to AI trained on
public writeups** — they reward method and creativity, and they are built to be
won by a human wielding an AI, not by an AI alone. That is the course thesis,
turned into a scoreboard.

**Read [ARCHITECTURE.md](ARCHITECTURE.md) first** — it has the research, the
novelty strategy, the full 12-challenge catalogue + 3 heavy labs, the CTFd
packaging plan, and the build order. This file is the operational quickstart.

---

## Status

| Piece | State |
|---|---|
| Research + architecture | ✅ complete ([ARCHITECTURE.md](ARCHITECTURE.md)) |
| `common/asp_reference.py` — the ASP VM model | ✅ built + validated |
| **REV track — all 5 challenges** | ✅ built end-to-end, logic verified |
| &nbsp;&nbsp;`rev/warmup-decoder` (intro, AI-calibration) | ✅ |
| &nbsp;&nbsp;`rev/padded-struct` (easy, S5 padding trap) | ✅ |
| &nbsp;&nbsp;`rev/signal-lock` (medium, transport-triggered VM) | ✅ |
| &nbsp;&nbsp;`rev/mirror` (medium, runtime keystream) | ✅ |
| &nbsp;&nbsp;`rev/asp-coprocessor` (hard, full VM + control flow) | ✅ |
| **CRYPTO track — both challenges** | ✅ built end-to-end, logic verified |
| &nbsp;&nbsp;`crypto/aura-license` (medium, ALC-64 keygen-me) | ✅ |
| &nbsp;&nbsp;`crypto/one-way-gate` (hard, anti-symbolic-execution) | ✅ |
| **MISC track — both challenges** | ✅ built end-to-end, **artifacts shipped** |
| &nbsp;&nbsp;`misc/firmware-triage` (easy-med, format parsing + decoy) | ✅ `dist/aura-fw.bin` real |
| &nbsp;&nbsp;`misc/blind-protocol` (medium, live service + pcap) | ✅ `dist/aura-capture.pcap` real, service tested |
| **PWN track — all 3 challenges** | ✅ built (design-complete; hosting = ops TODO) |
| &nbsp;&nbsp;`pwn/aurad-parser` (medium, signedness → ret2win) | ✅ logic verified |
| &nbsp;&nbsp;`pwn/telemetry-heap` (hard, tcache UAF → fptr) | ✅ logic verified |
| &nbsp;&nbsp;`pwn/asp-escape` (insane, VM escape via OOB write) | ✅ logic verified |
| labs (3) | 📐 specified, build next |

**All 12 challenges built.** Rev/crypto/misc are fully verified here (real
artifacts, solvers round-trip). Pwn is **design-complete**: correct vulnerable
source + reference exploit + writeup + reference Dockerfile, with the exploit
*logic* proven here and the full exploit proven on your Linux build host via
`healthcheck.sh`. Production jail/limits are documented in
[challenges/HOSTING.md](challenges/HOSTING.md) per the agreed scope.

Validate everything (offline, on any Python):

```bash
python3 common/check_rev_track.py      # 5 rev challenges
python3 common/check_crypto_track.py   # 2 crypto challenges
python3 common/check_misc_track.py     # 2 misc artifacts
python3 common/check_pwn_track.py      # 3 pwn logic models + source/Dockerfile/yml checks
# live/service + full-exploit proof (Linux host):
challenges/misc-blind-protocol/healthcheck.sh <host> <port>
challenges/pwn-*/healthcheck.sh        # needs gcc + pwntools
```

These parse every committed `.c`, run the arrays back through the verified
models, and assert accept/reject + solver round-trip + flag-matches-`challenge.yml`.
All green.

The reference challenge exists to prove the whole pipeline is real: a genuinely
novel machine (a transport-triggered architecture), a per-instance flag, a
stripped `dist/` artifact, a CTFd `challenge.yml`, a full writeup, and a reference
solver that recovers the flag from only what's observable. Its transform is proven
invertible over all inputs and its solver is proven per-instance robust (see
`common/asp_reference.py` and the healthcheck).

---

## Layout

```
ctf/
  ARCHITECTURE.md            the design (read first)
  common/
    asp_reference.py         validated model of the ASP VM (shared by several challenges)
  challenges/
    rev-signal-lock/         the built reference challenge
      challenge.yml          CTFd spec
      README.md              player prompt + host build notes
      src/gen.py             per-instance C generator (bakes flag -> expected[])
      src/signal-lock.c      generated source (do not hand-edit; regenerate)
      dist/                  ships ONLY the built binary
      solution/WRITEUP.md    full writeup + AI-failure-mode analysis
      solution/solve.py      reference solver / healthcheck
      Dockerfile             reproducible build
      healthcheck.sh         proves solvability; run in CI + before deploy
    ...                      (the other challenges, per ARCHITECTURE.md)
  labs/                      heavy multi-day projects (own-the-rig, build-a-breaker, blind-rig)
```

## Build & deploy one challenge

Everything builds in the course's Linux toolchain / Docker
(`../infra/SETUP.md`), not on Windows. Example, `signal-lock`:

```bash
cd challenges/rev-signal-lock
python3 src/gen.py --flag "AURA{your_flag_here}" > src/signal-lock.c
gcc -O2 -s -o dist/signal-lock src/signal-lock.c
./healthcheck.sh                 # MUST print OK before you ship
# set the same flag in challenge.yml, then:
ctf challenge install            # or: ctf challenge sync
```

## The rules we hold ourselves to (from ARCHITECTURE.md §7)

1. **CI proves solvability** — every challenge's `solve.py` recovers the flag from
   the freshly built artifact, or it doesn't ship.
2. **Re-verify against a current AI before each deployment** — record whether an
   unguided agent stalls (it should, on the novel ones). A wall that moved is a
   finding to teach from, not a failure to hide.
3. **Per-instance secrets** where a flag could leak — the method is the solution,
   never a memorised constant.
4. **Difficulty is measured** — track first-blood and solve counts; re-tier from
   data.

## For the team

Play them in tier order within a track. For each solve, keep the course's
hypothesis log (`../handouts/WORKSHEETS.md`). When you use AI — and you should —
note where it helped, where it misled you, and *how you knew*. That note is the
same muscle the whole course trained: use the machine, verify with evidence, be
the one who can tell when it's wrong.
