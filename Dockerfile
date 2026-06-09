FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    ABLETON_OSC_MCP_HOST=0.0.0.0 \
    ABLETON_OSC_MCP_PORT=8765 \
    ABLETON_OSC_HOST=host.docker.internal \
    ABLETON_OSC_PORT=11000 \
    ABLETON_OSC_REPLY_PORT=11001

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

RUN uv sync --frozen

EXPOSE 8765
EXPOSE 11001/udp

CMD ["uv", "run", "ableton-osc-mcp"]
