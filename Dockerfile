FROM python:3.12-slim-buster
RUN python -m pip install -U pip poetry
ENV PORT 8080
RUN mkdir /app
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
COPY . /app
RUN poetry install --no-interaction --no-ansi --no-root --only=main
CMD poetry run chick
