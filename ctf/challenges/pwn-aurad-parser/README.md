# Overrun
**pwn · medium (250, dynamic) · service-backed**

The AURA-7 command front-end validates the length of every command before it
reads it. Their words. We're not so sure. Get it to run its maintenance routine.

Download: `aurad-parser`   ·   Connect: `nc <HOST> 9010`

*(Host: [solution/WRITEUP.md](solution/WRITEUP.md), [../HOSTING.md](../HOSTING.md).
Ship only `dist/aurad-parser`; flag.txt is server-side, per-instance.)*
