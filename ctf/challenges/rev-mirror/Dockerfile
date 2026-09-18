# Build image for mirror (static-reversing challenge; no service).
#   docker build --build-arg FLAG='AURA{...}' -t mirror-build .
#   docker run --rm -v "$PWD/dist:/out" mirror-build
FROM gcc:13-bookworm AS build
ARG FLAG="AURA{wh4t_you_read_is_not_what_runs}"
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py --flag "$FLAG" > mirror.c  && gcc -O2 -s -o mirror mirror.c  && (strings mirror | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/mirror /out/mirror && echo 'built dist/mirror'"]
