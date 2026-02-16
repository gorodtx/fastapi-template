# Template: Runtime + Tests

## Runtime (default, cross-platform)

```bash
docker compose down -v --remove-orphans
docker compose up -d --build postgres redis migrate app nginx
```

Linux fallback для сред, где `bridge+ports` ломается (например `Empty reply`):

```bash
docker compose down -v --remove-orphans
docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

Если в build есть DNS-проблемы с PyPI, запускай с `DOCKER_BUILD_NETWORK=host`:

```bash
DOCKER_BUILD_NETWORK=host docker compose up -d --build postgres redis migrate app nginx
DOCKER_BUILD_NETWORK=host docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

Smoke check:

```bash
curl -i http://127.0.0.1:8080/system
curl -i http://127.0.0.1:8080/openapi.json
curl -i http://127.0.0.1:8080/docs
```

## Quality gates

```bash
make check
```

## Full live endpoint matrix (opt-in)

```bash
RUN_LIVE_E2E=1 E2E_BASE_URL=http://127.0.0.1:8080 uv run pytest tests/test_e2e_endpoint_matrix_live.py -q
```

Optional admin segment:

```bash
E2E_ADMIN_BEARER="<admin access token>"
```
