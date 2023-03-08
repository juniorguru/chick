# juniorguru-chick

A real-time, synchronous junior.guru Discord bot.

## Purpose

All junior.guru automation happens asynchronously (with up-to-24h delay), except of the following tasks provided by this bot:

-   Creating threads for #ahoj
-   Creating threads for #past-vedle-pasti
-   Creating threads for #můj-dnešní-objev

_Please, update the above list if adding features._

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

TODO https://jonahlawrence.hashnode.dev/hosting-a-python-discord-bot-for-free-with-flyio

## Design decisions

The asynchronous bot installs and uses this codebase to run the same code and perform the same tasks, idempotently:

-   If this bot crashes, the asynchronous bot will do the same stuff, just slower.
-   The purpose of this bot is to provide non-critical progressive enhancement, which can be dropped at any moment.
-   To keep the architecture simple, this bot should have no state.
    There should be no database.
    It should only react to the state and events of the Discord server, and write to the Discord server.
-   The synchronous bot should monitor whether this bot is up and running.
    If it's not, it should fail the build, but non-critically (similar to checking broken links).
