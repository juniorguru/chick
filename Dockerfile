FROM python:3.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set fake version for setuptools_scm so py-cord builds without Git
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PY_CORD=2.7.dev

ENV PORT 8080
RUN mkdir /app
WORKDIR /app
COPY pyproject.toml uv.lock /app/
COPY . /app
RUN uv sync
CMD uv run chick
