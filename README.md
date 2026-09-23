# ludo-star-club-manager

A standalone Ludo Star club manager with member tracking and a conversational browser bot.

## What this bot does

This project provides a **club-management assistant** for Ludo Star communities. It can:

- Add, list, find, and remove club members
- Track wins, losses, and games played
- Record notes for members
- Answer simple conversational commands from a browser
- Persist data locally in `members.json`

It intentionally does **not** automate Ludo Star gameplay, click through the game, manipulate accounts, or bypass anti-cheat systems.

## Run it

Requires Python 3.9 or newer.

```bash
python ludo_bot.py
```

Then open <http://localhost:8000> in your browser.

## Example messages

```text
help
add member Fatima
add member Alex
list members
record win Fatima
record loss Alex
stats Fatima
note Fatima captain of the weekend team
remove member Alex
```

The browser UI sends messages to the local bot and displays the conversation. Data is stored in `members.json` beside the application.

## API

The server also exposes:

- `GET /` — browser chat interface
- `POST /api/chat` with `{ "message": "list members" }`
- `GET /api/members` — JSON list of club members

This is a local starter bot. Add authentication and a database before deploying it publicly.
