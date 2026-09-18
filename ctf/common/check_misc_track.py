#!/usr/bin/env python3
"""Validate the misc-track challenges (offline checks).

firmware-triage : parse the SHIPPED dist/aura-fw.bin, recover the flag, confirm it
                  matches challenge.yml, confirm the decoy is present and the real
                  flag is NOT in plaintext.
blind-protocol  : re-verify the shipped pcap (checksums, stream payloads, and that
                  the two naive XOR constants differ), and confirm the server's
                  default flag matches challenge.yml.

Live service checks (auth trap + full solve) live in the challenge's
healthcheck.sh, which needs a running instance.
"""
import re, importlib.util, pathlib, struct, sys

ROOT = pathlib.Path(__file__).parents[1] / "challenges"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def yaml_flag(cdir):
    return re.search(r'content:\s*"([^"]+)"', (cdir / "challenge.yml").read_text()).group(1)

out = []

# ---------- firmware-triage ----------
d = ROOT / "misc-firmware-triage"
g = load(d / "src" / "gen.py", "fw_gen")
img = (d / "dist" / "aura-fw.bin").read_bytes()
flag = g.solve(img)
want = yaml_flag(d)
assert flag == want, f"firmware-triage: recovered {flag!r} != challenge.yml {want!r}"
assert g.DECOY_FLAG.encode() in img, "firmware-triage: decoy missing from shipped image"
assert flag.encode() not in img, "firmware-triage: REAL FLAG IS PLAINTEXT IN SHIPPED IMAGE"
payload_len, count = struct.unpack_from("<II", img, 0x08)
assert len(img) == 16 + 16 * count + payload_len + 4, "firmware-triage: layout arithmetic broken"
out.append(f"misc-firmware-triage  {len(img)}B  sections={count}  decoy present, real flag encoded  OK")

# ---------- blind-protocol ----------
d = ROOT / "misc-blind-protocol"
mp = load(d / "src" / "make_pcap.py", "bp_pcap")
buf, expected = mp.build()
npkt, nstream = mp.verify(buf, expected)
shipped = (d / "dist" / "aura-capture.pcap").read_bytes()
assert shipped == buf, "blind-protocol: shipped pcap differs from generator output"
# the trap must be *discoverable*: naive bytewise constants must differ across sessions
n1, n2 = 0x11223344, 0xAABBCCDD
t1 = ((n1 ^ mp.KEY) & 0xFFFFFFFF).to_bytes(4, "big")
t2 = ((n2 ^ mp.KEY) & 0xFFFFFFFF).to_bytes(4, "big")
c1 = bytes(x ^ y for x, y in zip(n1.to_bytes(4, "little"), t1))
c2 = bytes(x ^ y for x, y in zip(n2.to_bytes(4, "little"), t2))
assert c1 != c2, "blind-protocol: naive constants match — trap is invisible"
srv = (d / "src" / "server.py").read_text()
default_flag = re.search(r'AURA_FLAG",\s*"([^"]+)"', srv).group(1)
assert default_flag == yaml_flag(d), "blind-protocol: server default flag != challenge.yml"
assert "aura-capture.pcap" in (d / "challenge.yml").read_text(), "pcap not listed in files:"
out.append(f"misc-blind-protocol   pcap {len(shipped)}B  packets={npkt} streams={nstream}  "
           f"checksums OK, trap discoverable  OK")

print("\n".join(out))
print("\nALL MISC-TRACK ARTIFACTS VALIDATED  (live service checks: run each healthcheck.sh)")
