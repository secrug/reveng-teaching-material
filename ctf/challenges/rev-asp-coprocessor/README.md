# The Coprocessor
**rev · hard (450, dynamic)**

The AURA-7 board offloads its unlock check to a tiny coprocessor with a very
strange instruction set. We dumped its ROM and the checker it runs. Work out what
the coprocessor does, then find the input it accepts — that's the flag.

```
./asp-coprocessor     # reads one line from stdin
```
Download: `asp-coprocessor`

*(Host build/deploy notes: [solution/WRITEUP.md](solution/WRITEUP.md). Ship only `dist/asp-coprocessor`.)*
