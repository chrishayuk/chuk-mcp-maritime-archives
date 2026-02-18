# Maritime Archives MCP Server Dockerfile
# ===================================
# Multi-stage build for optimal image size

# Build stage
FROM python:3.14-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY scripts ./scripts

# Install the package (non-editable for Docker)
RUN uv pip install --system --no-cache .

# Download crew data from Zenodo (774K records, ~80MB)
RUN python scripts/download_crew.py || echo "Warning: crew download failed, demographics tools will return empty results"

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --from=builder /app/src ./src
COPY --from=builder /app/data ./data
COPY --from=builder /app/README.md ./
COPY --from=builder /app/pyproject.toml ./

RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    CHUK_ARTIFACTS_PROVIDER=memory

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); import chuk_mcp_maritime_archives; print('OK')" || exit 1

CMD ["python", "-m", "chuk_mcp_maritime_archives.server", "http", "--host", "0.0.0.0"]

EXPOSE 8005

LABEL description="Maritime Archives MCP Server - Historical Shipping Records & Wreck Databases" \
      version="0.18.1" \
      org.opencontainers.image.title="Maritime Archives MCP Server" \
      org.opencontainers.image.description="MCP server for historical maritime archives, VOC shipping records, and wreck databases"
