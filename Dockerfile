FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Chainlit looks for .chainlit/config.toml relative to CHAINLIT_APP_ROOT
ENV CHAINLIT_APP_ROOT=/app

# Install dependencies before copying source (better layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the project
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD uv run chainlit run coach/web/chainlit_app.py --host 0.0.0.0 --port ${PORT:-8000}
