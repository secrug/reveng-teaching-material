Ships to players. Must contain ONLY the built binary: one-way-gate
Build:  python3 src/gen.py > src/one-way-gate.c && gcc -O2 -s -o dist/one-way-gate src/one-way-gate.c
Built in the Linux toolchain/Docker. Delete this file before syncing.
