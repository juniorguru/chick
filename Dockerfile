FROM python:3.15-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*
ENV PORT 8080
RUN mkdir /app
WORKDIR /app
COPY pyproject.toml uv.lock /app/
COPY . /app
RUN uv sync
CMD uv run chick
