Ships to players. Must contain ONLY the built binary: mirror
Build:
  python3 src/gen.py --flag "AURA{...}" > src/mirror.c
  gcc -O2 -s -o dist/mirror src/mirror.c
Built in the Linux toolchain/Docker, not committed pre-built. Delete this file before syncing.
