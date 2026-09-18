Ships to players. Must contain ONLY the built binary: padded-struct
Build:
  python3 src/gen.py --flag "AURA{...}" > src/padded-struct.c
  gcc -O2 -s -o dist/padded-struct src/padded-struct.c
Built in the Linux toolchain/Docker, not committed pre-built. Delete this file before syncing.
