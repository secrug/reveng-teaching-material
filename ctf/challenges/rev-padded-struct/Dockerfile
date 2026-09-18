# Build image for padded-struct (static-reversing challenge; no service).
#   docker build --build-arg FLAG='AURA{...}' -t padded-struct-build .
#   docker run --rm -v "$PWD/dist:/out" padded-struct-build
FROM gcc:13-bookworm AS build
ARG FLAG="AURA{p4dding_is_where_the_model_slips}"
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py --flag "$FLAG" > padded-struct.c  && gcc -O2 -s -o padded-struct padded-struct.c  && (strings padded-struct | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/padded-struct /out/padded-struct && echo 'built dist/padded-struct'"]
