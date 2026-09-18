#!/usr/bin/env python3
"""misc/blind-protocol ("Cold Call") — the AURA-7 telemetry daemon.

Players get NO binary — only this service's address and a packet capture of two
successful sessions. They must infer the framing, the handshake, and the command
set from traffic alone, then talk to it.

Wire format (the thing to be reverse engineered):

    frame := u8 type | u16 length (BIG-endian) | payload[length]

    C->S 0x01 HELLO      "AURA7"
    S->C 0x81 HELLO_ACK  u32 nonce  (LITTLE-endian)      <-- endianness trap
    C->S 0x02 AUTH       u32 token  (BIG-endian), token = nonce_value ^ 0x5A3C1177
    S->C 0x82 AUTH_OK    "OK"   /  0xE2 AUTH_FAIL "NO"
    C->S 0x03 LIST       (empty)
    S->C 0x83 LIST_OK    u8 count | count x u8 item ids
    C->S 0x04 GET        u8 item id
    S->C 0x84 GET_OK     item bytes  /  0xE4 GET_ERR "??"

The nonce is fresh per connection, so the captured token cannot be replayed.
Item 0xFE holds the flag and is deliberately absent from the LIST response.
"""
import os, socket, socketserver, struct, threading

HOST, PORT = "0.0.0.0", int(os.environ.get("AURA_PORT", "9007"))
KEY = 0x5A3C1177
FLAG = os.environ.get("AURA_FLAG", "AURA{bl1nd_pr0tocol_n0_b1nary_needed}")

HELLO, AUTH, LIST, GET = 0x01, 0x02, 0x03, 0x04
HELLO_ACK, AUTH_OK, LIST_OK, GET_OK = 0x81, 0x82, 0x83, 0x84
AUTH_FAIL, GET_ERR = 0xE2, 0xE4

ITEMS = {
    0x01: b"unit=AURA-7 serial=7731-0042",
    0x02: b"uptime=184213s state=nominal",
    0x03: b"telemetry rate=4Hz buffer=ok",
    0xFE: FLAG.encode(),          # hidden: never appears in LIST
}
LISTED = [0x01, 0x02, 0x03]

def frame(t: int, payload: bytes = b"") -> bytes:
    return struct.pack("!BH", t, len(payload)) + payload

def read_frame(f):
    hdr = f.read(3)
    if len(hdr) < 3:
        return None, None
    t, n = struct.unpack("!BH", hdr)
    body = f.read(n) if n else b""
    if len(body) != n:
        return None, None
    return t, body

class Handler(socketserver.StreamRequestHandler):
    timeout = 30

    def handle(self):
        nonce = int.from_bytes(os.urandom(4), "little")
        authed = False
        try:
            while True:
                t, body = read_frame(self.rfile)
                if t is None:
                    return

                if t == HELLO:
                    if body != b"AURA7":
                        self.wfile.write(frame(AUTH_FAIL, b"NO")); return
                    # nonce goes out LITTLE-endian while frame lengths are BIG-endian
                    self.wfile.write(frame(HELLO_ACK, nonce.to_bytes(4, "little")))

                elif t == AUTH:
                    if len(body) != 4:
                        self.wfile.write(frame(AUTH_FAIL, b"NO")); continue
                    # token arrives BIG-endian
                    want = (nonce ^ KEY) & 0xFFFFFFFF
                    authed = (int.from_bytes(body, "big") == want)
                    self.wfile.write(frame(AUTH_OK, b"OK") if authed
                                     else frame(AUTH_FAIL, b"NO"))

                elif t == LIST:
                    if not authed:
                        self.wfile.write(frame(AUTH_FAIL, b"NO")); continue
                    self.wfile.write(frame(LIST_OK,
                                     bytes([len(LISTED)]) + bytes(LISTED)))

                elif t == GET:
                    if not authed:
                        self.wfile.write(frame(AUTH_FAIL, b"NO")); continue
                    if len(body) != 1 or body[0] not in ITEMS:
                        self.wfile.write(frame(GET_ERR, b"??")); continue
                    self.wfile.write(frame(GET_OK, ITEMS[body[0]]))

                else:
                    self.wfile.write(frame(GET_ERR, b"??"))
                self.wfile.flush()
        except (ConnectionError, socket.timeout):
            return

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    with Server((HOST, PORT), Handler) as srv:
        print(f"aurad listening on {HOST}:{PORT}", flush=True)
        srv.serve_forever()
