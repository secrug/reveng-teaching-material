#!/usr/bin/env python3
"""Layout-INDEPENDENT validation for the pwn track.

These challenges are memory-corruption exploits whose FULL verification needs a
Linux build + pwntools (each challenge's healthcheck.sh). What this script checks
without a compiler:
  * each challenge's reachability/logic model runs and asserts the bug is
    exploitable in principle,
  * the source is built with the required flags in the reference Dockerfile,
  * the source actually contains the intended win/unlock sink and the vuln marker,
  * challenge.yml uses the per-instance placeholder (no real flag baked in).
Run:  python3 ctf/common/check_pwn_track.py
"""
import importlib.util, pathlib, subprocess, sys, re

ROOT = pathlib.Path(__file__).parents[1] / "challenges"
PYTHON = sys.executable

def run_model(path):
    r = subprocess.run([PYTHON, str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"model {path.name} FAILED:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip().splitlines()[0]

def check(dirname, binname, model, needles, dockerflags="-fno-stack-protector -no-pie"):
    d = ROOT / dirname
    line = run_model(d / "src" / model)
    src = (d / "src" / f"{binname}.c").read_text()
    for n in needles:
        assert n in src, f"{dirname}: source missing expected marker {n!r}"
    dockerfile = (d / "Dockerfile").read_text()
    for f in dockerflags.split():
        assert f in dockerfile, f"{dirname}: Dockerfile missing build flag {f}"
    yml = (d / "challenge.yml").read_text()
    assert "REPLACE_AT_DEPLOY" in yml, f"{dirname}: challenge.yml should use the per-instance placeholder"
    assert f"dist/{binname}" in yml, f"{dirname}: binary not listed in files:"
    return f"{dirname:22} {line}"

out = []
out.append(check("pwn-aurad-parser", "aurad-parser", "verify_reach.py",
                 needles=["void unlock", "if (len > 64)", "(size_t)len", "int read_len_be32"]))
out.append(check("pwn-telemetry-heap", "telemetry-heap", "heap_model.py",
                 needles=["void win", "free(chans[i]);", "read(0, n, sizeof(struct chan))",
                          "chans[i]->fmt(chans[i])"]))
out.append(check("pwn-asp-escape", "asp-escape", "asp_escape_model.py",
                 needles=["void win", "unsigned char mem[64]", "void (*trap)",
                          "v.mem[v.reg[idx & 15]] = v.reg[s & 15]"]))

print("\n".join(out))
print("\nALL PWN-TRACK LOGIC VALIDATED  (full exploit proof: run each healthcheck.sh on a Linux host)")
