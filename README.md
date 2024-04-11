# Chick 🐤

A real-time, synchronous junior.guru Discord bot.

## Features

All junior.guru automation happens asynchronously (with up-to-24h delay) in the [main monolith codebase](https://github.com/juniorguru/junior.guru), except of the following tasks provided by this bot:

- [x] Creating threads in #past-vedle-pasti
- [x] Creating threads in #můj-dnešní-objev
- [x] Reacting to member-made threads in #práce-inzeráty
- [x] Reacting to member-made threads in #práce-hledám
- [x] Creating threads in #ahoj
- [x] Greeting new members in #ahoj
- [ ] Saving pins to members' DMs [#13](https://github.com/juniorguru/juniorguru-chick/issues/13)

_Please, update the above list if adding features._

## Design decisions

The original, asynchronous bot installs and uses this codebase to run the same code and perform the same tasks, idempotently:

-   If this bot crashes, the asynchronous bot will do the same stuff, just with a delay.
-   The purpose of this bot is to provide non-critical progressive enhancement, which can be dropped at any moment.
-   To keep the architecture simple, this bot should have no state.
    There should be no database.
    It should only react to the state and events of the Discord server, and write to the Discord server.
-   The asynchronous bot should monitor whether this bot is up and running.
    If it's not, it should fail the build, but non-critically (similar to checking broken links in HTML).

## Installation

1.  You'll need [poetry](https://python-poetry.org/) installed.
2.  Clone this repository: `git clone git@github.com:juniorguru/chick.git`
3.  Go to the project directory: `cd chick`
4.  Install the project: `poetry install`

## Development

Running locally:

-   Set the `DISCORD_API_KEY` environment variable to your Discord bot token.
    Using [direnv](https://direnv.net/) might help setting environment variables automatically in your shell when you navigate to the project directory.
-   Run `poetry run chick` to start the bot.
-   Press <kbd>Ctrl+C</kbd> to stop the bot.

Useful commands:

-   To test, run `pytest`.
-   To format code, run `ruff format`.
-   To organize imports and fix other issues, run `ruff check --fix`.

## Deployment

The bot is deployed to [fly.io](https://fly.io/).
Everything related to deployment is in the `Dockerfile`.
There's also `fly.toml`, but that's something the `flyctl` has generated and only they know what it is good for.

There is no need to deploy this bot manually.
Everything merged to the `main` branch of the GitHub repo gets automatically deployed to Fly.

For this to work, the output of `flyctl auth token` must be set as `FLY_API_TOKEN` secret in the GitHub repo settings.
The rest of the setup is in `.github/workflows/build.yml`.

If you insist to deploy manually from your local machine, follow these steps:

-   Have a hobby account at [fly.io](https://fly.io/).
-   Have a `flyctl` installed and be logged in.
-   Set the environment variable using `flyctl secrets set DISCORD_API_KEY=...`
-   Run `flyctl launch` in the project directory.
-   Run `flyctl deploy` if not deployed already.

_Inspired by [Hosting a Python Discord Bot for Free with Fly.io](https://jonahlawrence.hashnode.dev/hosting-a-python-discord-bot-for-free-with-flyio) by Jonah Lawrence._
