#!/usr/bin/env python3
"""Reference solver / healthcheck for firmware-triage.

Parses aura-fw.bin cold: header -> section table -> DATA section, decoded with
the BOOT section's CRC as the XOR key (as the loader banner hints). Verifies the
trailing checksum on the way, which is what proves you parsed the layout right.
"""
import argparse, struct, sys

def parse(buf: bytes):
    if buf[:4] != b"AURA":
        raise SystemExit("not an AURA firmware image")
    ver_major, ver_minor = struct.unpack_from("<HH", buf, 0x04)
    payload_len, count = struct.unpack_from("<II", buf, 0x08)
    entries = []
    for i in range(count):
        t, off, size, c = struct.unpack_from("<IIII", buf, 0x10 + 16 * i)
        entries.append((t.to_bytes(4, "little").decode(errors="replace"), off, size, c))
    return ver_major, ver_minor, payload_len, count, entries

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?", default="dist/aura-fw.bin")
    ap.add_argument("--live", action="store_true", help="healthcheck mode: assert flag recovered")
    a = ap.parse_args()
    buf = open(a.image, "rb").read()

    vmaj, vmin, payload_len, count, entries = parse(buf)
    print(f"AURA firmware v{vmaj}.{vmin}  filesize={len(buf)}  payload_len={payload_len}  sections={count}")
    print(f"  accounted: 16 header + {16*count} table + {payload_len} payload + 4 trailer "
          f"= {16 + 16*count + payload_len + 4}")
    for name, off, size, c in entries:
        print(f"  {name!r:8} off=0x{off:04x} size={size:<5} crc=0x{c:08x}")

    trailer = struct.unpack_from("<I", buf, len(buf) - 4)[0]
    calc = sum(buf[:-4]) & 0xFFFFFFFF
    print(f"  checksum: stored=0x{trailer:08x} computed=0x{calc:08x} "
          f"{'OK' if trailer == calc else 'MISMATCH'}")

    by = {n: (o, s, c) for n, o, s, c in entries}
    key = by["BOOT"][2].to_bytes(4, "little")          # "keyed by boot crc"
    off, size, _ = by["DATA"]
    flag = bytes(b ^ key[i % 4] for i, b in enumerate(buf[off:off + size])).decode(errors="replace")
    print(flag)

    if a.live:
        ok = flag.startswith("AURA{") and flag.endswith("}") and trailer == calc
        print(f"[healthcheck] {'OK' if ok else 'FAILED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
