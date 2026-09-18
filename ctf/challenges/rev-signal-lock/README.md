# Signal Lock

**Category:** rev · **Difficulty:** medium (250, dynamic)

We pulled the unlock verifier off an AURA-7 control board. It won't accept
anything we throw at it. Feed it the right signal and it unlocks — whatever you
fed it is the flag.

The chip is small. It is also not the chip you think it is.

```
./signal-lock       # reads one line from stdin
```

Download: `signal-lock`

---

*(Author/host notes for this challenge — build, deploy, the trick, and the
targeted AI failure mode — are in [solution/WRITEUP.md](solution/WRITEUP.md).
Do not ship this file's build section to players; the player-facing text is only
the block above, which mirrors `challenge.yml`'s `description`.)*

## Build & deploy (host only)

```bash
# 1. bake a per-instance flag into the C, then compile
python3 src/gen.py --flag "AURA{your_per_instance_flag}" > src/signal-lock.c
gcc -O2 -s -o dist/signal-lock src/signal-lock.c        # -s strips symbols

# 2. set the same flag in challenge.yml  (flags: content:)
# 3. sanity: the flag must NOT appear in the binary in plaintext
strings dist/signal-lock | grep -q "AURA{" && echo "LEAK - rebuild" || echo "clean"

# 4. prove it's solvable (dumps expected[] from the binary, inverts, re-runs)
./healthcheck.sh

# 5. ship: ctf challenge install && ctf challenge sync
```

Ship **only** `dist/signal-lock`. Never ship `src/`, `gen.py`, or `solution/`.
