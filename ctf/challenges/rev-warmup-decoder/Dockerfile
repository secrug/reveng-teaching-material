# Build image for warmup-decoder (static-reversing challenge; no service).
#   docker build --build-arg FLAG='AURA{...}' -t warmup-decoder-build .
#   docker run --rm -v "$PWD/dist:/out" warmup-decoder-build
FROM gcc:13-bookworm AS build
ARG FLAG="AURA{w4rmup_the_machine_is_good_at_this}"
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py --flag "$FLAG" > warmup-decoder.c  && gcc -O2 -s -o warmup-decoder warmup-decoder.c  && (strings warmup-decoder | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/warmup-decoder /out/warmup-decoder && echo 'built dist/warmup-decoder'"]
