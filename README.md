# juniorguru-chick

A real-time, synchronous junior.guru Discord bot.

## Purpose

All junior.guru automation happens asynchronously (with up-to-24h delay), except of the following tasks provided by this bot:

-   Creating threads for #ahoj
-   Creating threads for #past-vedle-pasti
-   Creating threads for #můj-dnešní-objev

_Please, update the above list if adding features._

## Design decisions

The asynchronous bot installs and uses this codebase to run the same code and perform the same tasks, idempotently:

-   If this bot crashes, the asynchronous bot will do the same stuff, just slower.
-   The purpose of this bot is to provide non-critical progressive enhancement, which can be dropped at any moment.
-   To keep the architecture simple, this bot should have no state.
    There should be no database.
    It should only react to the state and events of the Discord server, and write to the Discord server.
-   The synchronous bot should monitor whether this bot is up and running.
    If it's not, it should fail the build, but non-critically (similar to checking broken links).

## Installation

1.  You'll need [poetry](https://python-poetry.org/) installed.
2.  Clone this repository: `git clone git@github.com:juniorguru/juniorguru-chick.git`
3.  Go to the project directory: `cd juniorguru-chick`
4.  Install the project: `poetry install`

## Development

-   Set the `DISCORD_API_KEY` environment variable to your Discord bot token.
    Using [direnv](https://direnv.net/) might help setting environment variables automatically in your shell when you navigate to the project directory.
-   Run `poetry run jgc` to start the bot.
-   Press <kbd>Ctrl+C</kbd> to stop the bot.

## Deployment

The bot is deployed to [fly.io](https://fly.io/).
Everything related to deployment is in the `Dockerfile`.
There's also `fly.toml`, but that's something the `flyctl` has generated and only they know what it is good for.

There is no need to deploy this bot manually.
Everything merged to the `main` branch of the GitHub repo gets automatically deployed to Fly.

For this to work, the output of `flyctl auth token` must be set as `FLY_API_KEY` secret in the GitHub repo settings.
The rest of the setup is in `.github/workflows/build.yml`.

If you insist to deploy manually from your local machine, follow these steps:

-   Have a hobby account at [fly.io](https://fly.io/).
-   Have a `flyctl` installed and be logged in.
-   Set the environment variable using `flyctl secrets set DISCORD_API_KEY=...`
-   Run `flyctl launch` in the project directory.
-   Run `flyctl deploy` if not deployed already.

_Inspired by [Hosting a Python Discord Bot for Free with Fly.io](https://jonahlawrence.hashnode.dev/hosting-a-python-discord-bot-for-free-with-flyio) by Jonah Lawrence._
