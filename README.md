# juniorguru-chick

A real-time, synchronous junior.guru Discord bot.

## Installation

... TODO

## Purpose

All junior.guru automation happens asynchronously (with up-to-24h delay), except of the following tasks provided by this bot:

- Creating threads for #ahoj
- Creating threads for #past-vedle-pasti
- Creating threads for #můj-dnešní-objev

_Please, update the above list if adding features._

## Design decisions

The asynchronous bot installs and uses this codebase to run the same code and perform the same tasks, idempotently:

- If this bot crashes, the asynchronous bot will do the same stuff, just slower.
- The purpose of this bot is to provide non-critical progressive enhancement, which can be dropped at any moment.
- To keep the architecture simple, this bot should have no state. There should be no database. It should only react to the state and events of the Discord server, and write to the Discord server.
- The synchronous bot should monitor whether this bot is up and running. If it's not, it should fail the build, but non-critically (similar to checking broken links).
