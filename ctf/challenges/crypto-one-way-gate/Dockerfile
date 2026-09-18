# Build image for one-way-gate (static challenge; no service).
#   docker build -t one-way-gate-build .
#   docker run --rm -v "$PWD/dist:/out" one-way-gate-build
FROM gcc:13-bookworm AS build
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py > one-way-gate.c  && gcc -O2 -s -o one-way-gate one-way-gate.c  && (strings one-way-gate | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/one-way-gate /out/one-way-gate && echo 'built dist/one-way-gate'"]
