#!/usr/bin/env python3
"""Prove the blind-protocol endianness trap actually bites.

A player who captures ONE session and derives a naive bytewise constant
    C = nonce_wire XOR token_wire
will find it works for the captured nonce and FAILS against a fresh one, because
the real relation crosses byte orders (nonce LE in, token BE out). This script
asserts that:

  1. replaying the captured token is rejected  (fresh nonce per connection)
  2. the naive bytewise constant is rejected   (byte orders differ)
  3. the correct cross-endian token is accepted
"""
import socket, struct, sys

KEY = 0x5A3C1177
HELLO, AUTH = 0x01, 0x02
HELLO_ACK, AUTH_OK, AUTH_FAIL = 0x81, 0x82, 0xE2

def frame(t, p=b""): return struct.pack("!BH", t, len(p)) + p
def recv_frame(s):
    hdr = b""
    while len(hdr) < 3:
        c = s.recv(3 - len(hdr))
        if not c: raise SystemExit("closed")
        hdr += c
    t, n = struct.unpack("!BH", hdr)
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c: raise SystemExit("closed")
        b += c
    return t, b

def hello(s):
    s.sendall(frame(HELLO, b"AURA7"))
    t, body = recv_frame(s)
    assert t == HELLO_ACK
    return body                                  # raw 4 nonce bytes as seen on the wire

def try_token(host, port, token_bytes):
    with socket.create_connection((host, port), timeout=10) as s:
        nonce_wire = hello(s)
        s.sendall(frame(AUTH, token_bytes(nonce_wire)))
        t, _ = recv_frame(s)
        return t == AUTH_OK, nonce_wire

def correct(nonce_wire):
    return ((int.from_bytes(nonce_wire, "little") ^ KEY) & 0xFFFFFFFF).to_bytes(4, "big")

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9007

    # capture one legitimate session, as a player would from the pcap
    with socket.create_connection((host, port), timeout=10) as s:
        cap_nonce = hello(s)
        cap_token = correct(cap_nonce)
        s.sendall(frame(AUTH, cap_token))
        t, _ = recv_frame(s)
        assert t == AUTH_OK, "capture session should authenticate"
    naive_C = bytes(a ^ b for a, b in zip(cap_nonce, cap_token))

    ok_replay, _ = try_token(host, port, lambda n: cap_token)
    ok_naive,  _ = try_token(host, port,
                             lambda n: bytes(a ^ b for a, b in zip(n, naive_C)))
    ok_right,  _ = try_token(host, port, correct)

    print(f"captured nonce_wire = {cap_nonce.hex()}  token_wire = {cap_token.hex()}")
    print(f"naive bytewise constant C = {naive_C.hex()}")
    print(f"  replay captured token : {'ACCEPTED' if ok_replay else 'rejected'}  (want rejected)")
    print(f"  naive same-order XOR  : {'ACCEPTED' if ok_naive  else 'rejected'}  (want rejected)")
    print(f"  correct cross-endian  : {'ACCEPTED' if ok_right  else 'rejected'}  (want ACCEPTED)")

    assert not ok_replay, "replay should fail — nonce must be fresh per connection"
    assert not ok_naive,  "naive constant should fail — that IS the trap"
    assert ok_right,      "correct derivation must succeed"
    print("TRAP VERIFIED: challenge is not solvable by replay or naive XOR")

if __name__ == "__main__":
    main()
