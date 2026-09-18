# Hosting the service-backed challenges (pwn + blind-protocol)

This suite ships the pwn challenges as **design-complete** (vulnerable source,
reference exploit, writeup, and a *reference* Dockerfile) with **production
hardening deliberately left as a TODO for your infra team.** This file is that
TODO, written so it can be handed to whoever runs the CTFd deployment.

Applies to: `pwn/aurad-parser`, `pwn/telemetry-heap`, `pwn/asp-escape`, and (more
lightly) `misc/blind-protocol`.

---

## What the reference Dockerfiles do — and don't

Each pwn challenge's `Dockerfile` builds the binary with the intended flags
(`-O0 -fno-stack-protector -no-pie`) and exposes it with **`socat ... EXEC`**,
one forked process per connection. That is enough to *test* the challenge and to
run a small trusted event. It is **not** enough for a public CTF, because a
process reached over the network with an exploitable memory-corruption bug can be
driven to arbitrary code execution — which is the whole point — and nothing in
the reference image contains that code execution to the challenge.

**Do not run these on the public internet as-is.** Add the four controls below.

---

## The four production controls (the actual TODO)

### 1. Per-connection jail
Replace the bare `socat EXEC` with a real sandbox per connection. Two standard
options:

- **nsjail** (Google) — the common choice. Wrap the binary:
  ```
  socat TCP-LISTEN:9010,reuseaddr,fork \
    EXEC:'nsjail -Mo --chroot / --user 10001 --group 10001 \
          --time_limit 60 --rlimit_as 128 --disable_proc \
          --iface_no_lo -- /home/ctf/<bin>'
  ```
- **redpwn/jail** (`pwn.red/jail`) — a drop-in CTF jail image; put the binary in
  `/srv/app/run` and set `redpwn.pwn.jail` env. Handles nsjail config, seccomp,
  and per-connection isolation for you. Recommended if you don't already run
  nsjail.

### 2. Seccomp
The exploits only need to read a file and write stdout (`open/read/write/exit`,
and `execve("/bin/cat")` for the `system()`-based wins). Consider replacing the
`system("/bin/cat flag.txt")` in the `win()`/`unlock()` functions with a direct
`open`+`read`+`write` of `flag.txt` so you can apply a **tight seccomp allowlist**
that forbids `execve` entirely — a stronger containment that still lets the
intended solution work. (Left as your call; the challenges are written with
`system` for readability.)

### 3. Resource limits
Set at the jail and the container: CPU time (`--time_limit 60`), address space
(`rlimit_as`), process count (`pids_limit`), and memory (`mem_limit 128m`, already
in each `docker-compose.yml`). Prevents fork bombs and memory exhaustion from a
hostile or buggy exploit.

### 4. Per-instance flag injection
Never bake the real flag into the image. Inject `flag.txt` at deploy from your
secret store, `chmod 0444`, owned by a different uid than the service process
where possible, and **mirror the same value into each `challenge.yml`'s `flags:`
field.** The reference images write a `AURA{REPLACE_AT_DEPLOY}` placeholder
precisely so a missed injection fails loudly instead of leaking a real flag.

---

## Verifying a challenge before you open it

Every pwn challenge has a `healthcheck.sh` that (on a Linux host with
`gcc + python3 + pwntools`) builds the binary, runs the **reference exploit**
against it, and requires the flag to come back. Run it in CI and again against the
*deployed* instance (point the exploit at `HOST PORT`) before the challenge goes
visible. If the exploit doesn't land, the challenge is either mis-built (wrong
flags — check `-no-pie`/`-fno-stack-protector`) or the offset shifted on your
toolchain (see each writeup's "verify-on-build" note).

`blind-protocol` additionally ships `src/verify_trap.py`, which asserts the auth
trap still rejects replay and naive XOR against a running instance — run it too,
so a refactor can't silently make the challenge trivial.

---

## Difficulty / integrity re-check (suite policy)

Per `../ARCHITECTURE.md` §7: before each event, run each challenge's healthcheck
(solvability) **and** put the challenge through a current unguided AI agent
(resistance). Expected: the pwn and custom-VM challenges stall an unguided agent;
`warmup-decoder` falls to it. Record outcomes on the AI Scoreboard. A wall that
moved is a finding to teach from — bump difficulty or re-tier — never something to
paper over.
