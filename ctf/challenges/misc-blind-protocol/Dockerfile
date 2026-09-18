# AURA-7 telemetry daemon (blind-protocol service)
FROM python:3.12-slim
RUN useradd -m -u 10001 aura
WORKDIR /app
COPY src/server.py /app/server.py
ENV AURA_PORT=9007
ENV AURA_FLAG="AURA{bl1nd_pr0tocol_n0_b1nary_needed}"
USER aura
EXPOSE 9007
CMD ["python3", "-u", "/app/server.py"]
