#!/usr/bin/env python3
"""Build `aura-capture.pcap` — two complete, successful AURA-7 sessions.

Real libpcap/Ethernet/IPv4/TCP with correct IP and TCP checksums, so Wireshark's
"Follow TCP Stream" works properly. TWO sessions are included on purpose: with a
single one a player could derive a bytewise XOR constant that appears to work;
with two they can see that constant differs, which is the nudge toward the
cross-endian relation. Neither session performs the hidden GET 0xFE.

--verify reparses the file, reassembles both directions, checks every checksum,
and asserts the payloads are exactly the frames we intended.
"""
import argparse, struct, sys

KEY = 0x5A3C1177
CLIENT_IP, SERVER_IP = "10.0.0.2", "10.0.0.10"
CLIENT_MAC = bytes.fromhex("020000000002")
SERVER_MAC = bytes.fromhex("0200000000aa")
SERVER_PORT = 9007

HELLO, AUTH, LIST, GET = 0x01, 0x02, 0x03, 0x04
HELLO_ACK, AUTH_OK, LIST_OK, GET_OK = 0x81, 0x82, 0x83, 0x84

def frame(t, p=b""): return struct.pack("!BH", t, len(p)) + p
def ip2b(s): return bytes(int(x) for x in s.split("."))

def csum16(data: bytes) -> int:
    if len(data) % 2: data += b"\x00"
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) | data[i + 1]
    while s >> 16: s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF

def tcp_packet(src_ip, dst_ip, sport, dport, seq, ack, flags, payload=b""):
    tcp = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50, flags, 8192, 0, 0) + payload
    pseudo = ip2b(src_ip) + ip2b(dst_ip) + struct.pack("!BBH", 0, 6, len(tcp))
    c = csum16(pseudo + tcp)
    tcp = tcp[:16] + struct.pack("!H", c) + tcp[18:]

    total = 20 + len(tcp)
    ip = struct.pack("!BBHHHBBH", 0x45, 0, total, 0x1234, 0x4000, 64, 6, 0) + ip2b(src_ip) + ip2b(dst_ip)
    ip = ip[:10] + struct.pack("!H", csum16(ip)) + ip[12:]
    eth = (SERVER_MAC + CLIENT_MAC if src_ip == CLIENT_IP else CLIENT_MAC + SERVER_MAC)
    eth = (SERVER_MAC if src_ip == CLIENT_IP else CLIENT_MAC) + \
          (CLIENT_MAC if src_ip == CLIENT_IP else SERVER_MAC) + b"\x08\x00"
    return eth + ip + tcp

FIN, SYN, RST, PSH, ACK = 0x01, 0x02, 0x04, 0x08, 0x10

def session(sport, nonce, ts, packets):
    """Append one full session; returns the list of (direction, payload) exchanged."""
    cseq, sseq = 1000, 5000
    def c2s(flags, p=b""):
        nonlocal cseq
        packets.append((ts[0], tcp_packet(CLIENT_IP, SERVER_IP, sport, SERVER_PORT, cseq, sseq, flags, p)))
        ts[0] += 1
        cseq += len(p) + (1 if flags & (SYN | FIN) else 0)
    def s2c(flags, p=b""):
        nonlocal sseq
        packets.append((ts[0], tcp_packet(SERVER_IP, CLIENT_IP, SERVER_PORT, sport, sseq, cseq, flags, p)))
        ts[0] += 1
        sseq += len(p) + (1 if flags & (SYN | FIN) else 0)

    c2s(SYN); s2c(SYN | ACK); c2s(ACK)

    token = ((nonce ^ KEY) & 0xFFFFFFFF).to_bytes(4, "big")
    exchange = [
        ("c", frame(HELLO, b"AURA7")),
        ("s", frame(HELLO_ACK, nonce.to_bytes(4, "little"))),
        ("c", frame(AUTH, token)),
        ("s", frame(AUTH_OK, b"OK")),
        ("c", frame(LIST)),
        ("s", frame(LIST_OK, bytes([3]) + bytes([1, 2, 3]))),
        ("c", frame(GET, bytes([2]))),
        ("s", frame(GET_OK, b"uptime=184213s state=nominal")),
    ]
    for who, p in exchange:
        (c2s if who == "c" else s2c)(PSH | ACK, p)
    c2s(FIN | ACK); s2c(FIN | ACK); c2s(ACK)
    return exchange

def build():
    packets, ts = [], [1726500000]
    ex1 = session(51001, 0x11223344, ts, packets)
    ex2 = session(51002, 0xAABBCCDD, ts, packets)
    out = bytearray(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for i, (t, pkt) in enumerate(packets):
        out += struct.pack("<IIII", t, i * 1000, len(pkt), len(pkt)) + pkt
    return bytes(out), [ex1, ex2]

# ---------------- verification ----------------
def verify(buf, expected):
    magic, vmaj, vmin, tz, sf, snap, net = struct.unpack_from("<IHHiIII", buf, 0)
    assert magic == 0xA1B2C3D4 and net == 1, "bad pcap header"
    off = 24
    streams, npkt = {}, 0
    while off < len(buf):
        tss, tsu, incl, orig = struct.unpack_from("<IIII", buf, off); off += 16
        pkt = buf[off:off + incl]; off += incl; npkt += 1
        assert pkt[12:14] == b"\x08\x00", "not IPv4"
        ip = pkt[14:34]
        assert csum16(ip) == 0, "bad IP checksum"
        ihl = (ip[0] & 0xF) * 4
        total = struct.unpack_from("!H", ip, 2)[0]
        src, dst = ip[12:16], ip[16:20]
        tcp = pkt[14 + ihl: 14 + total]
        pseudo = src + dst + struct.pack("!BBH", 0, 6, len(tcp))
        assert csum16(pseudo + tcp) == 0, "bad TCP checksum"
        sport, dport = struct.unpack_from("!HH", tcp, 0)
        doff = (tcp[12] >> 4) * 4
        payload = tcp[doff:]
        if payload:
            key = sport if sport != SERVER_PORT else dport
            who = "c" if sport != SERVER_PORT else "s"
            streams.setdefault(key, []).append((who, payload))
    got = [streams[k] for k in sorted(streams)]
    assert len(got) == len(expected), f"{len(got)} streams, want {len(expected)}"
    for g, e in zip(got, expected):
        assert g == e, "stream payloads differ from intent"
    return npkt, len(got)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="dist/aura-capture.pcap")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    buf, expected = build()
    if a.verify:
        npkt, nstream = verify(buf, expected)
        n1 = 0x11223344; n2 = 0xAABBCCDD
        t1 = ((n1 ^ KEY) & 0xFFFFFFFF).to_bytes(4, "big")
        t2 = ((n2 ^ KEY) & 0xFFFFFFFF).to_bytes(4, "big")
        c1 = bytes(x ^ y for x, y in zip(n1.to_bytes(4, "little"), t1))
        c2 = bytes(x ^ y for x, y in zip(n2.to_bytes(4, "little"), t2))
        print("blind-protocol capture OK")
        print(f"  packets={npkt} streams={nstream} size={len(buf)}B  all IP+TCP checksums valid")
        print(f"  session1 nonce_wire={n1.to_bytes(4,'little').hex()} token={t1.hex()} naiveC={c1.hex()}")
        print(f"  session2 nonce_wire={n2.to_bytes(4,'little').hex()} token={t2.hex()} naiveC={c2.hex()}")
        assert c1 != c2, "the two naive constants must differ, or the trap is invisible"
        print("  naive constants DIFFER across sessions -> the trap is discoverable from the capture")
        return
    open(a.out, "wb").write(buf)
    sys.stderr.write(f"[gen] wrote {a.out} ({len(buf)} bytes)\n")

if __name__ == "__main__":
    main()
