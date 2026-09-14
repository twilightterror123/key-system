# Wisebyte deployment

This project is prepared to run on a Wisebyte VPS/server that supports Docker and Docker Compose.

## 1. Upload / clone the repository

Place the repository on the Wisebyte server and enter its directory.

## 2. Create the production environment

```bash
cp .env.wisebyte.example .env
nano .env
```

Set a long random `LICENSE_API_SECRET`. Keep `.env` private and never commit it.

## 3. Start the API

```bash
docker compose up -d --build
```

The API listens inside the container on port 8000. The health endpoint is:

```text
http://SERVER-IP:8000/health
```

It should return `{"ok":true}`.

## 4. Domain + HTTPS

Point your domain/subdomain (for example `keys.example.com`) to the Wisebyte server IP. Put the API behind the HTTPS reverse proxy provided by the hosting setup. The public client URL then becomes:

```text
https://keys.example.com
```

Do not expose the admin secret or the SQLite database publicly.

## 5. Admin API

Admin endpoints require the `X-API-Secret` header. Example:

```bash
curl -X POST https://keys.example.com/admin/create \
  -H 'Content-Type: application/json' \
  -H 'X-API-Secret: YOUR_SECRET' \
  -d '{"key_type":"1d"}'
```

For lifetime keys use `"key_type":"lifetime"`.

## 6. Updates

```bash
git pull
docker compose up -d --build
```

The named Docker volume `license_data` keeps `licenses.db` across container rebuilds.
