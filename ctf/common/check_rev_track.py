#!/usr/bin/env python3
"""Validate every rev-track challenge's COMMITTED .c against its verified model.

For each challenge: parse the const arrays out of the emitted C, then confirm
(a) the correct default flag is accepted / recovered, and (b) a mutation is
rejected. Catches C-emission/templating drift. Run from repo root:
    python3 ctf/common/check_rev_track.py
"""
import re, importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).parents[1] / "challenges"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def arr(txt, name):
    m = re.search(name + r"\[\]\s*=\s*\{([^}]*)\}", txt)
    return bytes(int(x, 0) for x in m.group(1).split(","))

def check_vm(cdir, cfile, flag, mut_idx, vm_path):
    vm = load(vm_path, "vm_" + cdir.name.replace("-", "_"))
    txt = (cdir/"src"/cfile).read_text()
    prog, exp = arr(txt, "prog"), arr(txt, "expected")
    fb = flag.encode()
    assert vm.run_vm(prog, fb, exp) is True, f"{cdir.name}: correct flag rejected"
    bad = bytearray(fb); bad[mut_idx] ^= 1
    assert vm.run_vm(prog, bytes(bad), exp) is False, f"{cdir.name}: mutation accepted"
    return f"{cdir.name:22} VM  prog={len(prog)}B exp={len(exp)}B  accept/reject OK"

def check_inline(cdir, cfile, flag, arrays, recover):
    g = load(cdir/"src"/"gen.py", cdir.name.replace("-", "_") + "_gen")
    txt = (cdir/"src"/cfile).read_text()
    got = {a: arr(txt, a) for a in arrays}
    rec = recover(g, got)
    assert rec == flag.encode(), f"{cdir.name}: recovered {rec!r} != {flag!r}"
    return f"{cdir.name:22} INL exp={len(got['expected'])}B  solver recovers flag OK"

COMMON = pathlib.Path(__file__).parents[0]
results = []
results.append(check_vm(ROOT/"rev-signal-lock", "signal-lock.c",
                        "AURA{tta_s1gnal_l0ck}", 7, COMMON/"asp_reference.py"))
results.append(check_vm(ROOT/"rev-asp-coprocessor", "asp-coprocessor.c",
                        "AURA{a_transport_triggered_l00p_w1th_branches}", 9,
                        ROOT/"rev-asp-coprocessor"/"src"/"gen.py"))
results.append(check_inline(ROOT/"rev-warmup-decoder", "warmup-decoder.c",
                        "AURA{w4rmup_the_machine_is_good_at_this}", ["expected"],
                        lambda g, d: bytes(g.invert(d["expected"][i], i) for i in range(len(d["expected"])))))
results.append(check_inline(ROOT/"rev-padded-struct", "padded-struct.c",
                        "AURA{p4dding_is_where_the_model_slips}", ["expected"],
                        lambda g, d: bytes(g.invert(d["expected"][i], i) for i in range(len(d["expected"])))))
results.append(check_inline(ROOT/"rev-mirror", "mirror.c",
                        "AURA{wh4t_you_read_is_not_what_runs}", ["CT", "expected"],
                        lambda g, d: g.invert(list(d["CT"]), list(d["expected"]))))

print("\n".join(results))
print("\nALL REV-TRACK COMMITTED C VALIDATED")
