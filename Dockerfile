FROM python:3.10-slim-buster
RUN python -m pip install -U pip poetry
ENV PORT 8080
RUN mkdir /app
COPY . /app
WORKDIR /app
RUN poetry install --no-interaction --no-ansi --no-root --no-dev
CMD poetry run jgc
