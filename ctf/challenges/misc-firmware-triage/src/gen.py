#!/usr/bin/env python3
"""misc/firmware-triage ("Teardown") — Easy-Medium/200.

Builds `aura-fw.bin`, a synthetic firmware image the player must parse cold.
No binary to reverse — the challenge IS the format.

Layout (all integers little-endian):
    0x00  char  magic[4]      "AURA"
    0x04  u16   ver_major     1
    0x06  u16   ver_minor     2
    0x08  u32   payload_len   sum of SECTION DATA only  <- deliberately != filesize
    0x0C  u32   section_count
    0x10  section table, section_count entries of 16 bytes:
              u32 type    FourCC ('BOOT','ASP ','DATA')
              u32 offset  absolute file offset of the section's data
              u32 size
              u32 crc     djb2-xor over the section's data
    ...   section payloads
    EOF-4 u32   checksum    sum of every byte from 0x00 up to end of payload

So: filesize = 16 (header) + 16*count (table) + payload_len + 4 (trailer).
`payload_len` alone matches neither the file size nor header+payload — this is
the same "the length field doesn't add up" puzzle the course opens with in S1,
and the missing bytes are the table and the checksum trailer.

The flag lives in the DATA section, XOR-encoded with the BOOT section's CRC
(the four bytes of that CRC, little-endian, repeating). The BOOT section carries
a decoy flag in plain ASCII plus the hint that the payload is "keyed by boot crc".

AI target: `strings` finds the DECOY first and a model reports it confidently.
Recovering the real flag needs exact offset arithmetic and correct field
association — the two things models reliably fumble.
"""
import argparse, struct, sys

REAL_FLAG  = "AURA{f1rmware_l4youts_d0nt_lie}"
DECOY_FLAG = "AURA{n0t_the_real_one_keep_looking}"

def crc(data: bytes) -> int:
    c = 0x1505
    for b in data:
        c = ((c * 33) ^ b) & 0xFFFFFFFF
    return c

def fourcc(s: str) -> int:
    return int.from_bytes(s.encode(), "little")

def asp_blob(n=96) -> bytes:
    """Flavour: plausible-looking coprocessor bytecode (deterministic)."""
    out = bytearray(); st = 0x13572468
    for _ in range(n):
        st = (st * 1103515245 + 12345) & 0xFFFFFFFF
        out.append((st >> 16) & 0xFF)
    return bytes(out)

def build(real_flag=REAL_FLAG, decoy=DECOY_FLAG) -> bytes:
    boot = (f"AURA-7 loader v1.2\n"
            f"stage1 ok\n"
            f"note: payload section is keyed by boot crc\n"
            f"debug-token: {decoy}\n").encode()
    asp  = asp_blob()
    key  = crc(boot).to_bytes(4, "little")
    data = bytes(b ^ key[i % 4] for i, b in enumerate(real_flag.encode()))

    sections = [("BOOT", boot), ("ASP ", asp), ("DATA", data)]
    count = len(sections)
    table_off = 0x10
    payload_off = table_off + 16 * count

    entries, blobs, off = [], [], payload_off
    for name, blob in sections:
        entries.append((fourcc(name), off, len(blob), crc(blob)))
        blobs.append(blob); off += len(blob)
    payload_len = sum(len(b) for b in blobs)

    out = bytearray()
    out += b"AURA"
    out += struct.pack("<HH", 1, 2)
    out += struct.pack("<I", payload_len)
    out += struct.pack("<I", count)
    for t, o, s, c in entries:
        out += struct.pack("<IIII", t, o, s, c)
    for b in blobs:
        out += b
    out += struct.pack("<I", sum(out) & 0xFFFFFFFF)   # trailer over everything before it
    return bytes(out)

# ---------- independent parser (this is what the player writes) ----------
def solve(buf: bytes) -> str:
    assert buf[:4] == b"AURA", "bad magic"
    payload_len, count = struct.unpack_from("<II", buf, 0x08)
    entries = [struct.unpack_from("<IIII", buf, 0x10 + 16 * i) for i in range(count)]
    by_name = {t.to_bytes(4, "little").decode(): (o, s, c) for t, o, s, c in entries}

    # integrity: trailer must match the sum of everything before it
    assert struct.unpack_from("<I", buf, len(buf) - 4)[0] == sum(buf[:-4]) & 0xFFFFFFFF, "bad checksum"
    assert payload_len == sum(s for _, s, _ in ((o, s, c) for o, s, c in by_name.values())), "payload_len mismatch"

    key = by_name["BOOT"][2].to_bytes(4, "little")      # the BOOT section's CRC field
    off, size, _ = by_name["DATA"]
    enc = buf[off:off + size]
    return bytes(b ^ key[i % 4] for i, b in enumerate(enc)).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="dist/aura-fw.bin")
    ap.add_argument("--flag", default=REAL_FLAG)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    buf = build(a.flag)

    if a.selftest:
        got = solve(buf)
        assert got == a.flag, f"solver got {got!r}"
        # the decoy must be findable by `strings` and the real flag must NOT be
        assert DECOY_FLAG.encode() in buf, "decoy missing"
        assert a.flag.encode() not in buf, "REAL FLAG IS IN PLAINTEXT — leak!"
        payload_len, count = struct.unpack_from("<II", buf, 0x08)
        print("firmware-triage OK")
        print(f"  filesize     = {len(buf)}")
        print(f"  payload_len  = {payload_len}   (filesize - payload_len = "
              f"{len(buf) - payload_len}  = 16 header + {16*count} table + 4 trailer)")
        print(f"  sections     = {count}")
        print(f"  decoy in file= yes   real flag in plaintext = no")
        print(f"  recovered    = {got}")
        return

    with open(a.out, "wb") as f:
        f.write(buf)
    sys.stderr.write(f"[gen] wrote {a.out} ({len(buf)} bytes) flag={a.flag!r}\n")

if __name__ == "__main__":
    main()
