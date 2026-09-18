# Build container for signal-lock. Produces dist/signal-lock reproducibly.
# Usage:
#   docker build --build-arg FLAG='AURA{...}' -t signal-lock-build .
#   docker run --rm -v "$PWD/dist:/out" signal-lock-build   # copies binary to dist/
#
# This is a BUILD image, not a service — signal-lock is a static-reversing
# challenge with no network component. (Contrast: the pwn/misc challenges ship a
# service Dockerfile + docker-compose.yml and set challenge.yml image/host.)
FROM gcc:13-bookworm AS build
ARG FLAG="AURA{tta_s1gnal_l0ck}"
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py --flag "$FLAG" > signal-lock.c \
 && gcc -O2 -s -o signal-lock signal-lock.c \
 && (strings signal-lock | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)

FROM scratch AS artifact
COPY --from=build /src/signal-lock /signal-lock

# default: emit the binary to a mounted /out
FROM build AS export
CMD ["sh", "-c", "cp /src/signal-lock /out/signal-lock && echo 'built dist/signal-lock'"]
