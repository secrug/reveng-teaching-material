Ships to players. Must contain ONLY the built binary: warmup-decoder
Build:
  python3 src/gen.py --flag "AURA{...}" > src/warmup-decoder.c
  gcc -O2 -s -o dist/warmup-decoder src/warmup-decoder.c
Built in the Linux toolchain/Docker, not committed pre-built. Delete this file before syncing.
