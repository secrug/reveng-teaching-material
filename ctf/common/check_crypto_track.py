#!/usr/bin/env python3
"""Validate the crypto-track challenges' COMMITTED .c against their models.

aura-license : parse SBOX/KEY/MAGIC out of the C, re-derive the unique licence,
               confirm it matches the reference solver AND the flag in challenge.yml.
one-way-gate : parse TABLE/ACC_TARGET out of the C, run the chunked brute-force
               solver, confirm it recovers the flag in challenge.yml.
Run from anywhere:  python3 ctf/common/check_crypto_track.py
"""
import re, importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).parents[1] / "challenges"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def barr(txt, name):
    m = re.search(r"unsigned char " + name + r"\[\]\s*=\s*\{([^}]*)\}", txt)
    return bytes(int(x, 0) for x in m.group(1).split(","))

def u32arr(txt, name):
    m = re.search(r"uint32_t " + name + r"\[\]\s*=\s*\{([^}]*)\}", txt)
    return [int(x.strip().rstrip("uU"), 0) for x in m.group(1).split(",")]

def scalar(txt, name):
    m = re.search(name + r"\s*=\s*([0-9]+)u", txt)
    return int(m.group(1))

def yaml_flag(cdir):
    txt = (cdir / "challenge.yml").read_text()
    return re.search(r'content:\s*"([^"]+)"', txt).group(1)

out = []

# ---------- aura-license ----------
d = ROOT / "crypto-aura-license"
g = load(d / "src" / "gen.py", "al_gen")
c = (d / "src" / "aura-license.c").read_text()
sbox, key, magic = barr(c, "SBOX"), barr(c, "KEY"), barr(c, "MAGIC")
assert sorted(sbox) == list(range(256)), "aura-license: SBOX in C is not a permutation"
assert list(sbox) == g.SBOX, "aura-license: SBOX in C != model SBOX"
assert magic == g.MAGIC, "aura-license: MAGIC mismatch"
ks = g.key_schedule(key)
lic = g.encrypt(magic, ks)
assert g.decrypt(lic, ks) == magic, "aura-license: licence does not decrypt to MAGIC"
flag = "AURA{" + lic.hex() + "}"
assert flag == yaml_flag(d), f"aura-license: flag {flag} != challenge.yml"
out.append(f"crypto-aura-license   sbox=256B key={key.hex()} licence={lic.hex()}  flag OK")

# ---------- one-way-gate ----------
d = ROOT / "crypto-one-way-gate"
g = load(d / "src" / "gen.py", "owg_gen")
c = (d / "src" / "one-way-gate.c").read_text()
table = u32arr(c, "TABLE")
acc_t = scalar(c, "ACC_TARGET")
rec = g.solve(table)                      # chunked brute force, 65536/chunk
expect = yaml_flag(d)
assert rec.decode() == expect, f"one-way-gate: recovered {rec!r} != {expect}"
assert g.path_acc(rec) == acc_t, "one-way-gate: checksum gate mismatch"
assert g.build_table(rec) == table, "one-way-gate: table mismatch"
out.append(f"crypto-one-way-gate   chunks={len(table)} acc={acc_t:#x}  solver recovers flag OK")

print("\n".join(out))
print("\nALL CRYPTO-TRACK COMMITTED C VALIDATED")
