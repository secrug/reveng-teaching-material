# Cold Call
**misc · medium (300, dynamic) · service-backed**

There's an AURA-7 telemetry daemon still answering on the plant network. We have
no firmware for it and no documentation — just a packet capture a technician took
before the vendor went quiet. Work out how to talk to it, then get it to tell you
something it shouldn't.

Download: `aura-capture.pcap`
Connect: `nc <HOST> 9007`

*(Host notes: [solution/WRITEUP.md](solution/WRITEUP.md). `docker compose up -d`,
set `AURA_FLAG` per instance and mirror it into `challenge.yml`. Ship only
`dist/aura-capture.pcap`.)*
