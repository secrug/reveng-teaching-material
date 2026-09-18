#!/usr/bin/env python3
"""Layout-INDEPENDENT verification for telemetry-heap.

I can't run glibc here, so this models the *semantics the exploit depends on* —
a tcache-style LIFO free-list with same-size reuse, plus the UAF (free does not
clear the app-level pointer) — and proves the exploit sequence lands &win in the
dangling channel's fmt slot. Actual chunk sizes/addresses are confirmed on the
built binary by healthcheck.sh; this proves the *logic* is sound."""

WIN = 0xDEADBEEF  # stand-in address; on the real non-PIE binary this is &win

class Heap:
    """Minimal tcache model: per-size LIFO bins; malloc reuses most-recent free."""
    def __init__(self):
        self.bins = {}          # size -> list (stack) of chunk ids
        self.mem = {}           # chunk id -> bytearray(size)
        self.next_id = 1
    def malloc(self, size):
        if self.bins.get(size):
            cid = self.bins[size].pop()          # reuse freed chunk (LIFO)
        else:
            cid = self.next_id; self.next_id += 1
            self.mem[cid] = bytearray(size)
        return cid
    def free(self, cid, size):
        self.bins.setdefault(size, []).append(cid)   # chunk goes back; contents linger

CHAN = 32
DEFAULT_FMT = 0xCAFE0000    # stand-in for &default_fmt

def run_exploit():
    h = Heap()
    chans = {}                                   # index -> chunk id (app pointer)
    fmt = {}                                      # chunk id -> current fmt value (offset 0)

    # new(0)
    c0 = h.malloc(CHAN); chans[0] = c0; fmt[c0] = DEFAULT_FMT
    # del(0)  -- BUG: chans[0] still points at c0
    h.free(c0, CHAN)
    assert chans[0] == c0, "app pointer must remain (this is the UAF)"
    # note(p64(&win)) -- malloc(32) returns c0; first 8 bytes overwrite fmt
    n = h.malloc(CHAN)
    assert n == c0, "tcache must return the freed channel chunk"
    fmt[n] = WIN                                  # attacker writes &win at offset 0
    # show(0) -- calls chans[0]->fmt, which now aliases the note's first 8 bytes
    called = fmt[chans[0]]
    return called

if __name__ == "__main__":
    called = run_exploit()
    assert called == WIN, f"show(0) would call {called:#x}, not win"
    print("telemetry-heap reachability OK")
    print("  sequence new(0); del(0); note(p64(&win)); show(0)")
    print(f"  => dangling chans[0]->fmt is called with attacker value ({WIN:#x} == &win)")
    print("  => win() -> cat flag.txt")
    print("  (chunk size/addr + tcache bin index confirmed on the build by healthcheck.sh)")
