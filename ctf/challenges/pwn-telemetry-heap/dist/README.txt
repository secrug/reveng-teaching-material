Ships to players. Must contain ONLY the built binary: telemetry-heap
Build:  gcc -O0 -fno-stack-protector -no-pie -o dist/telemetry-heap src/telemetry-heap.c
Players get the binary (to reverse offline) AND a live service to exploit.
NEVER ship flag.txt or src/. Delete this file before syncing.
