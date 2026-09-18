# Build image for asp-coprocessor (static-reversing challenge; no service).
#   docker build --build-arg FLAG='AURA{...}' -t asp-coprocessor-build .
#   docker run --rm -v "$PWD/dist:/out" asp-coprocessor-build
FROM gcc:13-bookworm AS build
ARG FLAG="AURA{a_transport_triggered_l00p_w1th_branches}"
WORKDIR /src
COPY src/gen.py .
RUN apt-get update && apt-get install -y python3 --no-install-recommends
RUN python3 gen.py --flag "$FLAG" > asp-coprocessor.c  && gcc -O2 -s -o asp-coprocessor asp-coprocessor.c  && (strings asp-coprocessor | grep -q 'AURA{' && (echo 'FLAG LEAKED IN BINARY' >&2; exit 1) || true)
FROM build AS export
CMD ["sh","-c","cp /src/asp-coprocessor /out/asp-coprocessor && echo 'built dist/asp-coprocessor'"]
