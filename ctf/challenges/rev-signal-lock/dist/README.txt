This directory ships to players. It must contain ONLY the built binary:

    signal-lock

Build it with (from the challenge root):
    python3 src/gen.py --flag "AURA{...}" > src/signal-lock.c
    gcc -O2 -s -o dist/signal-lock src/signal-lock.c

The binary is produced in the Linux toolchain / Docker (see ../../../../infra/SETUP.md),
not committed pre-built, so the per-instance flag is baked at deploy time.
Delete this README.txt before syncing the challenge.
