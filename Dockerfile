FROM python:3.11-slim-buster
RUN python -m pip install -U pip poetry
ENV PORT 8080
RUN mkdir /app
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-interaction --no-ansi --no-root --only-main
COPY . /app
CMD poetry run jgc
