## Local run (single command, always via Nginx entrypoint)

Start everything with one command:

```bash
./nginx/up.sh
```

What this does:
- starts `postgres`, `redis`, `app`, and `nginx` via `docker compose`
- runs migrations inside `app` container before starting `uvicorn`
- keeps public entrypoint only at `http://localhost:8080`
- proxies all traffic `nginx -> app:8000` in compose network
- uses your local project virtualenv (`.venv`) mounted into the `app` container

Prerequisite (once):

```bash
uv sync
```

Use API through:

```text
http://localhost:8080
```

Swagger (dev): `http://localhost:8080/docs`  
OpenAPI: `http://localhost:8080/openapi.json`

### Stop stack

```bash
./nginx/down.sh
```

### Logs

```bash
docker compose logs -f app nginx
```

### Nginx rate limit

Nginx config lives in:
- `nginx/nginx.conf`
- `nginx/conf.d/app.conf`

Auth routes protected by edge limits:
- `/auth/login` and `/auth/login/`
- `/auth/register` and `/auth/register/`
- `/auth/refresh` and `/auth/refresh/`

`/auth/login` also has connection limit (`limit_conn`).
