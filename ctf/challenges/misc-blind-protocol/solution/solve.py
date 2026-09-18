#!/usr/bin/env python3
"""Reference solver / healthcheck for blind-protocol.

Everything here was inferred from the capture:
  * framing      : u8 type | u16 length BIG-endian | payload
  * handshake    : HELLO "AURA7" -> HELLO_ACK carrying a 4-byte nonce
  * the trap     : the nonce is LITTLE-endian while frame lengths are BIG-endian,
                   and the token goes back BIG-endian. Cross the byte orders or
                   the server rejects you on every fresh connection.
  * token        : (nonce_as_LE_u32 ^ 0x5A3C1177) sent as BIG-endian u32
  * item 0xFE    : not in LIST — found by enumerating the 1-byte id space
"""
import argparse, socket, struct, sys

KEY = 0x5A3C1177
HELLO, AUTH, LIST, GET = 0x01, 0x02, 0x03, 0x04
HELLO_ACK, AUTH_OK, LIST_OK, GET_OK = 0x81, 0x82, 0x83, 0x84

def frame(t, payload=b""):
    return struct.pack("!BH", t, len(payload)) + payload

def recv_frame(s):
    hdr = b""
    while len(hdr) < 3:
        c = s.recv(3 - len(hdr))
        if not c: raise SystemExit("connection closed")
        hdr += c
    t, n = struct.unpack("!BH", hdr)
    body = b""
    while len(body) < n:
        c = s.recv(n - len(body))
        if not c: raise SystemExit("connection closed")
        body += c
    return t, body

def handshake(s):
    s.sendall(frame(HELLO, b"AURA7"))
    t, body = recv_frame(s)
    assert t == HELLO_ACK and len(body) == 4, f"unexpected {t:#x}"
    nonce = int.from_bytes(body, "little")            # LE off the wire
    token = (nonce ^ KEY) & 0xFFFFFFFF
    s.sendall(frame(AUTH, token.to_bytes(4, "big")))  # BE back
    t, body = recv_frame(s)
    if t != AUTH_OK:
        raise SystemExit(f"auth failed ({t:#x} {body!r}) — check your byte order")
    return nonce

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9007)
    ap.add_argument("--live", action="store_true", help="healthcheck: require a flag")
    a = ap.parse_args()

    with socket.create_connection((a.host, a.port), timeout=10) as s:
        nonce = handshake(s)
        print(f"[+] authed (nonce={nonce:#010x})")

        s.sendall(frame(LIST))
        t, body = recv_frame(s)
        listed = list(body[1:1 + body[0]]) if t == LIST_OK else []
        print(f"[+] LIST advertises: {[hex(i) for i in listed]}")

        found = {}
        for i in range(256):                       # the id space is one byte — enumerate it
            s.sendall(frame(GET, bytes([i])))
            t, body = recv_frame(s)
            if t == GET_OK:
                found[i] = body
        hidden = [i for i in found if i not in listed]
        print(f"[+] GET answers for: {[hex(i) for i in found]}  (hidden: {[hex(i) for i in hidden]})")

        flag = None
        for i, v in found.items():
            if b"AURA{" in v:
                flag = v.decode(errors="replace")
        print(flag if flag else "[-] no flag found")

    if a.live:
        ok = bool(flag and flag.startswith("AURA{"))
        print(f"[healthcheck] {'OK' if ok else 'FAILED'}", file=sys.stderr)
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
