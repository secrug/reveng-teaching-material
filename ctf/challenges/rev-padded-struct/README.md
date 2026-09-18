# Wire Format
**rev · easy (150, dynamic)**

The AURA-7 config loader checks each byte of your input against a table of "steps"
baked into the firmware. Get the table right and the wire format validates — the
accepted input is the flag.

```
./padded-struct       # reads one line from stdin
```
Download: `padded-struct`

*(Host build/deploy notes: [solution/WRITEUP.md](solution/WRITEUP.md). Ship only `dist/padded-struct`.)*
