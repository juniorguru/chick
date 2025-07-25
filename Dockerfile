FROM python:3.12-slim-bookworm
RUN python -m pip install -U pip poetry==1.8.5

# Set fake version for setuptools_scm so py-cord builds without Git
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PY_CORD=2.7.dev

ENV PORT 8080
RUN mkdir /app
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
COPY . /app
RUN poetry install --no-interaction --no-ansi --no-root --only=main
CMD poetry run chick
