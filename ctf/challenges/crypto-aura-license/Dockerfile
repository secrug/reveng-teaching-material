# Build image for aura-license (static challenge; no service).
#   docker build -t aura-license-build .
#   docker run --rm -v "$PWD/dist:/out" aura-license-build
FROM gcc:13-bookworm AS build
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py > aura-license.c  && gcc -O2 -s -o aura-license aura-license.c  && (strings aura-license | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/aura-license /out/aura-license && echo 'built dist/aura-license'"]
