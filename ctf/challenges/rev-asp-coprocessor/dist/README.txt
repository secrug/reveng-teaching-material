Ships to players. Must contain ONLY the built binary: asp-coprocessor
Build:
  python3 src/gen.py --flag "AURA{...}" > src/asp-coprocessor.c
  gcc -O2 -s -o dist/asp-coprocessor src/asp-coprocessor.c
Built in the Linux toolchain/Docker, not committed pre-built. Delete this file before syncing.
