## Local run

1) Ensure Postgres and Redis are running (local or Docker).
2) Load environment variables:

```bash
set -a
source .env
set +a
```

3) Start the API:

```bash
uv run uvicorn --app-dir src backend.main:create_app --factory --reload --port 8000
```

Swagger is available at `/docs` in dev mode.  
Set `APP_ENV=prod` to disable `/docs` and `/openapi.json`.
