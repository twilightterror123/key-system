# TWILIGHT Key System — Wisebyte

Production-ready license server layout for a Wisebyte VPS/container.

## Features

- 1-day and lifetime keys
- First activation binds a key to one installation
- Revocation
- Plaintext keys are returned only when created; the database stores SHA-256 hashes
- FastAPI HTTP API
- Discord slash commands: `/genkey`, `/revoke`, `/keys`
- SQLite database persisted in a Docker volume
- No secrets committed to GitHub

## Deploy on Wisebyte

1. Put this repository on your Wisebyte server.
2. Copy `.env.example` to `.env`.
3. Set `DISCORD_TOKEN` to your Discord bot token.
4. Set `LICENSE_API_SECRET` to a long random secret. Do not publish it.
5. Keep `LICENSE_API_URL=http://key-server:8000` when the bot runs through the included Compose setup.
6. Start the stack:

```bash
docker compose up -d --build
```

7. Test the API from the server:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"ok":true,"service":"twilight-key-server"}
```

## Public domain

For a public HTTPS address, put the API behind the HTTPS reverse proxy provided/configured on your Wisebyte server. The public client URL should then be your HTTPS domain, for example:

`https://keys.example.com`

Do not expose the admin secret or `.env` publicly.

## Client

Use `client/license_client.py` from your application and pass the public HTTPS base URL. The client creates a random installation ID locally and sends it with activation.

## Important

GitHub stores the source code. Wisebyte runs the live server. The database is runtime data and is intentionally ignored by Git.
