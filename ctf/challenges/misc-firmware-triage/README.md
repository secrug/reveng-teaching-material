# Teardown
**misc · easy-medium (200, dynamic)**

We pulled the firmware image off an AURA-7 control board. Engineering swears
there's a build token in there somewhere, but the one we found doesn't work.
Take the image apart properly.

Download: `aura-fw.bin`

*(Host notes: [solution/WRITEUP.md](solution/WRITEUP.md). No compiler needed —
`python3 src/gen.py -o dist/aura-fw.bin` produces the artifact. Ship only
`dist/aura-fw.bin`.)*
