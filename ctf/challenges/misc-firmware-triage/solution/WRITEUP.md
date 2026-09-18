# Teardown — Writeup

**Category:** misc/forensics (RE crossover) · **Difficulty:** easy–medium
**Flag:** `AURA{f1rmware_l4youts_d0nt_lie}`

## TL;DR

`aura-fw.bin` is a firmware image with a header, a section table and a trailing
checksum. `strings` hands you a **decoy** flag immediately. The real one is in the
`DATA` section, XOR-encoded with the **`BOOT` section's CRC** — which is sitting
right there in the section table. Parse the layout properly and it falls out.

## 1. First contact

```
$ file aura-fw.bin
aura-fw.bin: data
$ strings aura-fw.bin
AURA-7 loader v1.2
stage1 ok
note: payload section is keyed by boot crc
debug-token: AURA{n0t_the_real_one_keep_looking}
```

Two things there, and only one of them is a gift. The `debug-token` is a decoy —
submit it and you get a rejection. The *actually* useful string is the note:
**"payload section is keyed by boot crc."** Remember it.

## 2. The header, and the length that doesn't add up

```
$ xxd aura-fw.bin | head -4
00000000: 4155 5241 0100 0200 f800 0000 0300 0000  AURA............
00000010: 424f 4f54 4000 0000 7900 0000 2f21 ef81  BOOT@...y.../!..
00000020: 4153 5020 b900 0000 6000 0000 4744 7f13  ASP ...`...GD..
00000030: 4441 5441 1901 0000 1f00 0000 e1d6 801d  DATA........
```

```
0x00  "AURA"                  magic
0x04  01 00  02 00            u16 major=1, u16 minor=2   (little-endian)
0x08  f8 00 00 00             u32 payload_len = 248
0x0C  03 00 00 00             u32 section_count = 3
0x10  section table, 16 bytes each: { u32 type, u32 offset, u32 size, u32 crc }
```

The file is **316** bytes but `payload_len` says **248**. That 68-byte gap is the
whole triage exercise:

```
316 = 16 (header) + 48 (3 x 16-byte table entries) + 248 (payload) + 4 (checksum trailer)
```

`payload_len` counts *section data only*. This is exactly the "the length field
doesn't match `ls -l`" open question from Session 1 of the course — and the answer
is the same one it always is: the field counts something specific, and the
remainder is structure you haven't accounted for yet.

Verify the trailer to prove you've parsed it right: the last `u32` is the sum of
every preceding byte, `0x785f`. If that matches, your layout is correct.

## 3. Decode the payload

The table gives you everything:

| type | offset | size | crc |
|---|---|---|---|
| `BOOT` | 0x0040 | 121 | `0x81ef212f` |
| `ASP ` | 0x00b9 | 96 | `0x137f4447` |
| `DATA` | 0x0119 | 31 | `0x1d80d6e1` |

"Keyed by boot crc" → take `BOOT`'s CRC field, `0x81ef212f`, as four
little-endian bytes `2f 21 ef 81`, and XOR it repeating over the `DATA` section:

```python
key = (0x81ef212f).to_bytes(4, "little")
flag = bytes(b ^ key[i % 4] for i, b in enumerate(data))
# AURA{f1rmware_l4youts_d0nt_lie}
```

```
$ python3 solve.py aura-fw.bin
AURA firmware v1.2  filesize=316  payload_len=248  sections=3
  accounted: 16 header + 48 table + 248 payload + 4 trailer = 316
  checksum: stored=0x0000785f computed=0x0000785f OK
AURA{f1rmware_l4youts_d0nt_lie}
```

(The `ASP ` section is coprocessor bytecode — flavour, and a deliberate rabbit
hole. It contains nothing you need.)

## 4. Why this is hard for AI (the targeted failure)

This challenge has no code to read, which removes the model's strongest surface
and leaves the two things it is measurably worst at.

1. **The lazy path yields a confident wrong answer.** Ask a model "what's the flag
   in this file?" and it will run the equivalent of `strings`, find
   `AURA{n0t_the_real_one_keep_looking}`, and report it — because it *looks* exactly
   like a flag, in a field literally named `debug-token`. This is the S1 scoreboard
   entry ("invented behaviour from strings") in its purest form: the model is not
   lying, it's answering a question adjacent to the one you asked. Nothing about
   the output signals that a decoy was even possible.
2. **Exact offset arithmetic and field association.** Getting the real flag needs
   a 16-byte stride over the table, correct little-endian field reads, and the
   insight that `BOOT`'s CRC keys `DATA`'s payload — associating a field from one
   record with the contents of another. Offsets and cross-record association are
   precisely where models drift, and here a single wrong offset yields garbage
   rather than a near-miss.

The human method is unglamorous and reliable: account for **every byte** in the
file. The moment `316 - 248 = 68` gets decomposed into `16 + 48 + 4`, the format
is understood and the rest is arithmetic. Teach the team to distrust any flag
that arrives without that accounting having been done.

## 5. Mitigation note

A "debug token" that looks like a credential, left in a shipped image, is a real
and common finding — as is keying a payload with a value stored in the clear
three fields away. Obscurity in a container format buys nothing once the format is
understood; the only thing protecting `DATA` here is that you have to read the
table, which takes about five minutes.
