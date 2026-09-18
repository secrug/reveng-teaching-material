# Reference service image for telemetry-heap.
# PRODUCTION HARDENING IS A TODO — see ../HOSTING.md. This image uses socat to
# expose the binary and applies basic limits, but a real deployment MUST add a
# per-connection jail (nsjail / redpwn jail), seccomp, and resource caps.
FROM gcc:13-bookworm AS build
WORKDIR /src
COPY src/telemetry-heap.c .
RUN gcc -O0 -fno-stack-protector -no-pie -o telemetry-heap telemetry-heap.c

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y socat --no-install-recommends && rm -rf /var/lib/apt/lists/*  && useradd -m -u 10001 ctf
WORKDIR /home/ctf
COPY --from=build /src/telemetry-heap ./telemetry-heap
# flag.txt is injected at deploy (per-instance); never bake it into the image.
RUN echo 'AURA{REPLACE_AT_DEPLOY}' > flag.txt && chown -R ctf:ctf /home/ctf && chmod 0444 flag.txt
USER ctf
EXPOSE 9010
# one process per connection; add nsjail here in production (see HOSTING.md)
CMD ["socat", "-T60", "TCP-LISTEN:9010,reuseaddr,fork", "EXEC:./telemetry-heap,stderr"]
