Ships to players. Must contain ONLY the built binary: aura-license
Build:  python3 src/gen.py > src/aura-license.c && gcc -O2 -s -o dist/aura-license src/aura-license.c
Built in the Linux toolchain/Docker. Delete this file before syncing.
