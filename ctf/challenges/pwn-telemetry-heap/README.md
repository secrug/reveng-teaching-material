# Ring Zero
**pwn · hard (400, dynamic) · service-backed**

The AURA-7 telemetry manager lets you create, delete, annotate and display
channels. It's careful about indices. It is not careful about lifetimes.

Download: `telemetry-heap`   ·   Connect: `nc <HOST> 9010`

*(Host: [solution/WRITEUP.md](solution/WRITEUP.md), [../HOSTING.md](../HOSTING.md).
Ship only `dist/telemetry-heap`; flag.txt is server-side, per-instance.)*
