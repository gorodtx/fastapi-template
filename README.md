# FastAPI Clean/DDD Template

[English](#english) | [Русский](#русский)

Production-oriented backend template: FastAPI + Clean/DDD + SQLAlchemy + Postgres + Redis + Alembic + JWT.

## Quick Deploy / Быстрый запуск

Release / Релиз: <https://github.com/gorodtx/fastapi-template/releases/latest>

Use release tag (например `v1.0.0`) and run one command:

```bash
TAG=v1.0.0 && git clone --depth 1 --branch "$TAG" https://github.com/gorodtx/fastapi-template.git && cd fastapi-template && cp .env.example .env && docker compose -f compose/data.yaml up -d && DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml run --rm migrate && DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/app.yaml up -d --build
```

What to use from release / Что использовать из релиза:

- clone by semantic tag (`git clone --branch vX.Y.Z`) as the single install path / клон по тегу — единый путь установки
- `.env.example` -> `.env` with real credentials before first start / реальные значения перед стартом
- runtime files from tag: `compose/`, `nginx/`, `migrations/`, `alembic.ini`, `src/`

Smoke checks / Проверка:

- `curl -i http://127.0.0.1:8080/system`
- `curl -i http://127.0.0.1:8080/openapi.json`
- `curl -i http://127.0.0.1:8080/docs`

## Technology Stack / Стек технологий

### Runtime

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?logo=uvicorn&logoColor=white)](https://www.uvicorn.org/)
[![Dishka](https://img.shields.io/badge/Dishka-DI-4B5563)](https://github.com/reagento/dishka)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![asyncpg](https://img.shields.io/badge/asyncpg-driver-2D3748)](https://github.com/MagicStack/asyncpg)
[![Alembic](https://img.shields.io/badge/Alembic-migrations-8A2BE2)](https://alembic.sqlalchemy.org/)

[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)](https://nginx.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

[![PyJWT](https://img.shields.io/badge/PyJWT-JWT-111827)](https://pyjwt.readthedocs.io/)
[![Argon2](https://img.shields.io/badge/Argon2-password%20hashing-0F766E)](https://argon2-cffi.readthedocs.io/)
[![msgspec](https://img.shields.io/badge/msgspec-serialization-7C3AED)](https://jcristharif.com/msgspec/)
[![environs](https://img.shields.io/badge/environs-config-334155)](https://github.com/sloria/environs)

### Tooling & Quality

[![uv](https://img.shields.io/badge/uv-package%20manager-6A5ACD)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/Ruff-lint%2Fformat-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![ty](https://img.shields.io/badge/ty-type%20check-1F2937)](https://github.com/astral-sh/ty)
[![Pytest](https://img.shields.io/badge/Pytest-tests-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

[![GitHub Actions CI](https://github.com/gorodtx/fastapi-template/actions/workflows/ci.yml/badge.svg)](https://github.com/gorodtx/fastapi-template/actions/workflows/ci.yml)
[![make check required](https://img.shields.io/badge/make%20check-required-2ea44f)](#10-quality-and-tests)
[![live e2e opt-in](https://img.shields.io/badge/live%20e2e-opt--in-0a66c2)](#10-quality-and-tests)
[![GitHub Release](https://img.shields.io/github/v/release/gorodtx/fastapi-template)](https://github.com/gorodtx/fastapi-template/releases/latest)

---

## English

### 1) What this template gives you

- Clear layer boundaries:
  - `domain`: pure business rules and policies
  - `application`: use-case orchestration via ports
  - `infrastructure`: DB/cache/security adapters
  - `presentation`: HTTP routes/schemas/DI
- Runtime stack:
  - FastAPI + Dishka DI
  - Postgres (`asyncpg` + SQLAlchemy)
  - Redis
  - Alembic migrations
  - JWT access/refresh flow
- Quality gates:
  - `ruff` + `ty` + `pytest` via `make check`

### 2) Architecture and transaction model

- Request lifecycle:
  - one request-scoped `AsyncSession`
  - one request-scoped `TransactionManager`
- Write use-cases run in short transactions (`run_result_in_tx` + `manager.transaction()`).
- Write transaction wrapper retries the whole use-case on transient DB failures (`db.transient.*`) with bounded exponential backoff.
- Nested behavior is explicit:
  - `nested=True` -> savepoint (`begin_nested`)
  - already-inside scope -> no extra scope (`nullcontext`)
  - existing DB transaction without scope -> controlled commit/rollback scope
- `current_user` auth lookup uses a short-lived dedicated DB session on cache miss, so auth-read does not alter the write transaction boundary of the request.
- Startup behavior:
  - app factory builds `Settings` from env and disables docs/openapi in `prod|production`
  - DI is wired via `setup_di(app, settings)` with Dishka route integration
  - app-level `AppError` handler sanitizes payload/meta and maps status codes
  - `assert_closed_by_default(app)` enforces auth dependency for non-public routes

### 3) RBAC contract: versioned role/permission catalog

Role/permission **catalog** is seeded and versioned through migrations.  
Public API still does **not** create roles or permissions; API only assigns/revokes roles for users.

Current system roles (`SystemRole`):

- `super_admin`
- `admin`
- `user`

Current permission codes (`PermissionCode`):

- `users:read`
- `users:create`
- `users:update`
- `users:delete`
- `rbac:read_roles`
- `rbac:assign_role`
- `rbac:revoke_role`

Current registry (`ROLE_PERMISSIONS`):

- `user`: empty permission set
- `admin`: full admin set above
- `super_admin`: currently same as admin (prepared for extension later)

Additional roles/permissions can be added via migration template (`20260209_0003`), then assigned through API.

### 4) Database schema and table relations

Core tables are created in bootstrap migration `20260203_0001`:

- `users`
  - `id` UUID PK
  - `email` unique
  - `login` unique
  - `username` unique
  - `password_hash`
  - `is_active`
- `roles`
  - `id` UUID PK
  - `code` unique
  - `description`
- `permissions`
  - `code` PK
  - `description`
- `role_permissions` (many-to-many role <-> permission)
  - PK: (`role_id`, `permission_code`)
  - FK `role_id -> roles.id` (CASCADE)
  - FK `permission_code -> permissions.code` (CASCADE)
- `user_roles` (many-to-many user <-> role)
  - PK: (`user_id`, `role_id`)
  - FK `user_id -> users.id` (CASCADE)
  - FK `role_id -> roles.id` (CASCADE)

Relation chain for authorization:

`users -> user_roles -> roles -> role_permissions -> permissions`

### 5) RBAC migration mechanism (how role/permission changes are made)

#### 5.1 Bootstrap migration

`migrations/versions/20260203_0001_bootstrap_rbac.py`:

1. creates `users`, `roles`, `permissions`, `role_permissions`, `user_roles`
2. creates indexes on relation tables
3. seeds:
   - all system roles
   - all permission codes
   - role-permission links from `ROLE_PERMISSIONS`
4. optionally bootstraps users from env var `RBAC_BOOTSTRAP_USERS`

`RBAC_BOOTSTRAP_USERS` format (JSON list, optional):

```json
[
  {
    "email": "owner@example.com",
    "login": "owner",
    "username": "owner",
    "password": "StrongPass123!",
    "roles": ["super_admin"]
  }
]
```

If `roles` is omitted, default is `["super_admin"]`.

#### 5.2 Adding/changing role-permission mappings

Use template `migrations/templates/roles_permissions_template.py`:

1. create new revision
   - `uv run alembic revision -m "rbac update"`
2. copy template into the new revision file
3. fill required payload:
   - `revision`, `down_revision`
   - `NEW_ROLES: dict[str, frozenset[str]]`
4. optionally fill:
   - `SUPER_ADMIN_EXTRA_PERMISSIONS`
   - `ROLE_DESCRIPTIONS`
   - `ROLE_USER_BINDINGS` (role -> tuple of user logins)
5. apply:
   - `uv run alembic upgrade head`

Template behavior:

- validates role/permission code formats
- requires non-empty permission set per declared role
- upserts roles and permissions
- synchronizes role-permission links (adds missing, removes extra)
- can bind existing users to roles by login
- idempotent: re-running keeps target state
- downgrade removes only roles declared in that migration payload

### 6) Environment setup

Create your own `.env` from `.env.example` and fill it with real values:

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_ALG`
- `JWT_SECRET`
- `JWT_ACCESS_TTL_S`
- `JWT_REFRESH_TTL_S`
- `DEFAULT_REGISTRATION_ROLE_CODE`
- `AUTH_USER_CACHE_TTL_S`
- refresh-lock settings:
  - `REFRESH_LOCK_TTL_S`
  - `REFRESH_LOCK_WAIT_TIMEOUT_S`
- pool/timeout settings:
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
  - `DB_POOL_TIMEOUT_S`
  - `DB_POOL_RECYCLE_S`
  - `DB_CONNECT_TIMEOUT_S`
- Argon2 settings:
  - `ARGON2_TIME_COST`
  - `ARGON2_MEMORY_COST_KIB`
  - `ARGON2_PARALLELISM`
  - `ARGON2_HASH_LEN`
  - `ARGON2_SALT_LEN`
- observability settings (`OBS_OTEL_*`):
  - `OBS_OTEL_ENABLED`
  - `OBS_OTEL_SERVICE_NAME`
  - `OBS_OTEL_SERVICE_VERSION`
  - `OBS_OTEL_ENVIRONMENT`
  - `OBS_OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OBS_OTEL_METRICS_EXPORT_INTERVAL_MS`
  - `OBS_OTEL_HTTP_INSTRUMENTATION_ENABLED`
  - `OBS_OTEL_CAPTURE_REQUEST_HEADERS`
  - `OBS_OTEL_CAPTURE_RESPONSE_HEADERS`
  - `OBS_OTEL_SANITIZE_FIELDS_CSV`
- observability runtime settings:
  - `OBS_OTEL_GRPC_PORT`
  - `OBS_PROMETHEUS_PORT`
  - `OBS_GRAFANA_PORT`
  - `OBS_ALERTMANAGER_PORT`
  - `OBS_LOKI_PORT`
  - `OBS_ALLOY_PORT`
  - `OBS_TEMPO_HTTP_PORT`
  - `OBS_LOKI_RETENTION_PERIOD`

Production notes:

- use strong secrets and real credentials
- keep `.env` out of git
- docs/openapi are disabled when `APP_ENV` is `prod` or `production`

### 7) Runtime

Compose scopes (modular runtime):

- `compose/data.yaml` — Postgres + Redis
- `compose/migrate.yaml` — one-shot schema/bootstrap step
- `compose/app.yaml` — app + nginx
- `compose/release.yaml` — release overlay (pull-only images, no build)
- `compose/obs.yaml` — OTel/Prometheus/Grafana/Loki/Tempo/Alertmanager/VictoriaMetrics
- `compose/core.hostnet.yaml` — Linux host-network override for Postgres/Redis
- `compose/migrate.hostnet.yaml` — Linux host-network override for migrate
- `compose/app.hostnet.yaml` — Linux host-network override for app/nginx
- `compose/obs.hostnet.yaml` — Linux host-network override for observability

Core runtime (data + migrate + app):

```bash
docker compose -f compose/data.yaml down -v --remove-orphans
docker compose -f compose/data.yaml up -d
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/app.yaml up -d --build
```

Release runtime (prebuilt images, no server build):

```bash
export APP_IMAGE=ghcr.io/<owner>/fastapi-template-app:vX.Y.Z
export MIGRATE_IMAGE=ghcr.io/<owner>/fastapi-template-migrate:vX.Y.Z
export NGINX_IMAGE=ghcr.io/<owner>/fastapi-template-nginx:vX.Y.Z
# Optional for local smoke with prebuilt local tags:
# export RELEASE_PULL_POLICY=missing

docker compose -f compose/data.yaml up -d
docker compose -f compose/data.yaml -f compose/migrate.yaml -f compose/release.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/release.yaml up -d
```

Core + observability:

```bash
OBS_OTEL_ENABLED=true docker compose -f compose/data.yaml -f compose/app.yaml -f compose/obs.yaml up -d --build
```

Linux host-network fallback (use when host cannot read Docker-published ports):

```bash
docker compose -f compose/data.yaml -f compose/core.hostnet.yaml down -v --remove-orphans
docker compose -f compose/data.yaml up -d
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml -f compose/core.hostnet.yaml -f compose/migrate.hostnet.yaml run --rm migrate
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/app.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml up -d --build
OBS_OTEL_ENABLED=true docker compose -f compose/data.yaml -f compose/app.yaml -f compose/obs.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml -f compose/obs.hostnet.yaml up -d
```

If `curl` returns `000` on host (`Empty reply from server`):

1. This is usually a host Docker networking/runtime issue, not an app failure.
2. Verify service from inside Docker network first:

```bash
docker run --rm --network <project>_default curlimages/curl:8.12.1 -s -o /dev/null -w '%{http_code}\n' http://nginx:8080/system
```

3. Use host-network fallback for this machine:

```bash
docker compose -f compose/data.yaml -f compose/app.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml up -d --build
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/system
```

Standard service ports:

- app: `8080`
- postgres: `5432`
- redis: `6379`
- OTel gRPC: `4317` (with `compose/obs.yaml`)
- Prometheus-1: `9090` (with `compose/obs.yaml`)
- Prometheus-2: `9091` (with `compose/obs.yaml`)
- Grafana: `3000` (with `compose/obs.yaml`)
- Alertmanager-1: `9093` (with `compose/obs.yaml`)
- Alertmanager-2: `9193` (with `compose/obs.yaml`)
- Loki: `3100` (with `compose/obs.yaml`)
- Alloy: `12345` (with `compose/obs.yaml`)
- Tempo: `3200` (with `compose/obs.yaml`)
- VictoriaMetrics: `8428` (with `compose/obs.yaml`)

If a standard port is occupied, free it manually before start (or stop conflicting containers/processes).

Nginx auth rate limits are configurable via compose env vars:

- `AUTH_LOGIN_RATE`
- `AUTH_REGISTER_RATE`
- `AUTH_REFRESH_RATE`

Runtime entrypoints:

- `compose/migrate.yaml` (`migrate.command`) -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `compose/app.yaml` (`app.command`) -> `uv run --no-dev --no-sync --frozen uvicorn ...`
- `compose/release.yaml` -> image-only app/migrate/nginx services with `pull_policy: ${RELEASE_PULL_POLICY:-always}` (release deploy without local build)

App-only horizontal scaling (data/obs scopes are untouched):

```bash
docker compose -f compose/data.yaml -f compose/app.yaml up -d --scale app=3
```

Observability stack (enabled by adding `-f compose/obs.yaml` and setting `OBS_OTEL_ENABLED=true` for app):

- OTel Collector config: `ops/otel-collector/config.yaml`
- Prometheus scrape config: `ops/prometheus/prometheus.yml`, `ops/prometheus/prometheus-2.yml`
- Prometheus rules: `ops/prometheus/rules/recording.yml`, `ops/prometheus/rules/alerts.yml`
- Alertmanager config template: `ops/alertmanager/alertmanager.yml`
- Alertmanager runtime render script: `ops/alertmanager/render-config.sh`
- Loki config: `ops/loki/loki.yml`
- Alloy config: `ops/alloy/config.alloy`
- Tempo config: `ops/tempo/tempo.yml`
- Grafana datasource provisioning: `ops/grafana/provisioning/datasources/datasources.yml`
- Grafana dashboards provisioning: `ops/grafana/provisioning/dashboards/dashboards.yml`
- App OTEL is disabled by default in compose (`OBS_OTEL_ENABLED=false`)
- Observability ports are bound to localhost (`127.0.0.1`) in default compose mode
- Collector gRPC is exposed on `${OBS_OTEL_GRPC_PORT}` (default `4317`) for local debugging
- Prometheus-1 UI: `http://127.0.0.1:${OBS_PROMETHEUS_PORT}` (default `9090`)
- Prometheus-2 UI: `http://127.0.0.1:${OBS_PROMETHEUS_REPLICA_PORT}` (default `9091`)
- Grafana UI: `http://127.0.0.1:${OBS_GRAFANA_PORT}` (default `3000`, credentials `admin/admin`; override via `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- Alertmanager-1 UI: `http://127.0.0.1:${OBS_ALERTMANAGER_PORT}` (default `9093`)
- Alertmanager-2 UI: `http://127.0.0.1:${OBS_ALERTMANAGER_REPLICA_PORT}` (default `9193`)
- Loki API: `http://127.0.0.1:${OBS_LOKI_PORT}` (default `3100`)
- Alloy UI: `http://127.0.0.1:${OBS_ALLOY_PORT}` (default `12345`)
- Tempo UI/API: `http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}` (default `3200`)
- VictoriaMetrics UI/API: `http://127.0.0.1:${OBS_VICTORIAMETRICS_PORT}` (default `8428`)
- Prometheus retention is configurable via `OBS_PROMETHEUS_RETENTION` (default `24h`) and persisted in a Docker volume
- Alertmanager retention is configurable via `ALERTMANAGER_RETENTION` (default `120h`) and persisted in a Docker volume
- `X-Trace-Id` response header is emitted only when a valid active trace exists
- Collector OTLP receiver uses bearer auth (`OBS_OTEL_AUTH_TOKEN` in collector, `OBS_OTEL_EXPORTER_OTLP_HEADERS` in app)
- App OTLP exporter supports optional TLS/mTLS files:
  - `OBS_OTEL_EXPORTER_OTLP_CA_CERT_FILE`
  - `OBS_OTEL_EXPORTER_OTLP_CLIENT_CERT_FILE`
  - `OBS_OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE`
- Optional runtime instrumentation flags:
  - `OBS_OTEL_SQLALCHEMY_INSTRUMENTATION_ENABLED=true` instruments SQLAlchemy engine on creation
  - `OBS_OTEL_REDIS_INSTRUMENTATION_ENABLED=true` enables Redis client instrumentation
- Collector derives span-to-metrics for dependency visibility (DB/Redis) via `spanmetrics` connector:
  - Spanmetrics are generated in a dedicated traces pipeline without tail sampling; tail sampling is applied only on the Tempo export path.
  - `traces_spanmetrics_calls_total`
  - `traces_spanmetrics_duration_seconds_bucket`
- Grafana datasources are configured via env:
  - `GRAFANA_PROMETHEUS_URL`
  - `GRAFANA_PROMETHEUS_LTS_URL`
  - `GRAFANA_LOKI_URL`
  - `GRAFANA_TEMPO_URL`
- Prometheus replicas remote-write to VictoriaMetrics for long-term retention (`/api/v1/write`)
- Alertmanager webhook endpoints are configured via env:
  - `ALERTMANAGER_WEBHOOK_TICKET_URL`
  - `ALERTMANAGER_WEBHOOK_PAGE_URL`
  - `ALERTMANAGER_WEBHOOK_HEARTBEAT_URL`
- Optional direct channels (in addition to webhooks):
  - `ALERTMANAGER_TICKET_SLACK_WEBHOOK_URL`
  - `ALERTMANAGER_PAGE_SLACK_WEBHOOK_URL`
  - `ALERTMANAGER_PAGE_PAGERDUTY_ROUTING_KEY`
- In `APP_ENV=prod`, set non-default `GRAFANA_ADMIN_PASSWORD` and non-local Alertmanager receiver URLs before startup.

Prometheus now has shortcut recording series for day-to-day use:

- `service:rps:5m`
- `service:error_rate_5xx:5m`
- `service:latency_p95_ms:5m`
- `dependency:db_redis_error_rate_pct:5m`
- `dependency:db_redis_latency_p95_seconds:5m`
- Plus monitoring-of-monitoring rules:
  - `NoHTTPMetricsData`, `NoCollectorMetricsData`, `Watchdog`
  - `CollectorExporterQueueSaturation`
  - `CollectorReceiverRefusedData`
  - `CollectorExporterSendFailures`
  - `AlertmanagerNotificationFailures`
- Dependency alerts:
  - `HighDependencyErrorRate`
  - `HighDependencyP95Latency`
- Alert notifications are sent only after a rule stays firing for its `for` duration.

Pre-provisioned Grafana dashboards:

- `Service RED`
- `Platform Observability`
- `Service RED` includes `Service`/`Dependency` filters, dependency alert drill-down links, and Tempo Explore links.
- `Start Here (Overview)` is provisioned as the Grafana home dashboard with only core health signals.

### 8) API surface (current)

Current OpenAPI paths:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /system`
- `POST /users`
- `GET /users/me`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /rbac/users/{user_id}/roles`
- `POST /rbac/users/{user_id}/roles`
- `DELETE /rbac/users/{user_id}/roles/{role_code}`

### 9) Smoke checks

```bash
curl -i http://127.0.0.1:8080/system
curl -i http://127.0.0.1:8080/openapi.json
curl -i http://127.0.0.1:8080/docs
```

### 10) Quality and tests

Run full quality gates:

```bash
make check
```

Live endpoint matrix (opt-in):

```bash
RUN_LIVE_E2E=1 E2E_BASE_URL=http://127.0.0.1:8080 uv run pytest tests/test_e2e_endpoint_matrix_live.py -q
```

Optional admin segment for live matrix:

```bash
E2E_ADMIN_BEARER="<admin access token>"
```

---

## Русский

### 1) Что даёт шаблон

- Чёткие границы слоёв:
  - `domain`: чистые бизнес-правила и политики
  - `application`: orchestration use-case через порты
  - `infrastructure`: адаптеры БД/кеша/безопасности
  - `presentation`: HTTP-роуты/схемы/DI
- Runtime-стек:
  - FastAPI + Dishka DI
  - Postgres (`asyncpg` + SQLAlchemy)
  - Redis
  - Alembic-миграции
  - JWT access/refresh
- Контроль качества:
  - `ruff` + `ty` + `pytest` через `make check`

### 2) Архитектура и модель транзакций

- На один HTTP-запрос:
  - одна request-scoped `AsyncSession`
  - один request-scoped `TransactionManager`
- Write use-case выполняются в короткой транзакции (`run_result_in_tx` + `manager.transaction()`).
- Обертка write-транзакции повторяет весь use-case на transient DB-ошибках (`db.transient.*`) с ограниченным exponential backoff.
- Поведение вложенности:
  - `nested=True` -> savepoint (`begin_nested`)
  - если scope уже открыт -> без доп. scope (`nullcontext`)
  - если внешняя транзакция уже есть, но scope нет -> контролируемый commit/rollback scope
- `current_user` при cache miss использует отдельную короткоживущую DB-session, чтобы auth-read не менял границу write-транзакции текущего запроса.
- Поведение старта:
  - фабрика приложения собирает `Settings` из env и отключает docs/openapi в `prod|production`
  - DI подключается через `setup_di(app, settings)` и интеграцию Dishka routes
  - app-level `AppError` handler санитизирует payload/meta и маппит status codes
  - `assert_closed_by_default(app)` проверяет auth dependency для непубличных роутов

### 3) RBAC-контракт: версионируемый каталог ролей/прав

Каталог ролей/прав сидируется и версионируется миграциями.  
Публичный API **не** создаёт роли и permission’ы; API только назначает/снимает роли у пользователей.

Текущие системные роли (`SystemRole`):

- `super_admin`
- `admin`
- `user`

Текущие permission-коды (`PermissionCode`):

- `users:read`
- `users:create`
- `users:update`
- `users:delete`
- `rbac:read_roles`
- `rbac:assign_role`
- `rbac:revoke_role`

Текущий реестр (`ROLE_PERMISSIONS`):

- `user`: пустой набор прав
- `admin`: полный admin-набор выше
- `super_admin`: сейчас равен `admin` (подготовлена точка расширения)

Дополнительные роли/права можно добавлять миграционным шаблоном (`20260209_0003`), а затем назначать через API.

### 4) Схема БД и связи таблиц

Основные таблицы создаются миграцией `20260203_0001`:

- `users`
  - `id` UUID PK
  - `email` unique
  - `login` unique
  - `username` unique
  - `password_hash`
  - `is_active`
- `roles`
  - `id` UUID PK
  - `code` unique
  - `description`
- `permissions`
  - `code` PK
  - `description`
- `role_permissions` (many-to-many роль <-> permission)
  - PK: (`role_id`, `permission_code`)
  - FK `role_id -> roles.id` (CASCADE)
  - FK `permission_code -> permissions.code` (CASCADE)
- `user_roles` (many-to-many пользователь <-> роль)
  - PK: (`user_id`, `role_id`)
  - FK `user_id -> users.id` (CASCADE)
  - FK `role_id -> roles.id` (CASCADE)

Цепочка для авторизации:

`users -> user_roles -> roles -> role_permissions -> permissions`

### 5) Механизм RBAC-миграций (как менять роли/права)

#### 5.1 Bootstrap-миграция

`migrations/versions/20260203_0001_bootstrap_rbac.py`:

1. создаёт `users`, `roles`, `permissions`, `role_permissions`, `user_roles`
2. создаёт индексы на связующих таблицах
3. сидирует:
   - все системные роли
   - все permission-коды
   - связи роль-права из `ROLE_PERMISSIONS`
4. опционально создаёт bootstrap-пользователей из `RBAC_BOOTSTRAP_USERS`

Формат `RBAC_BOOTSTRAP_USERS` (JSON-массив, опционально):

```json
[
  {
    "email": "owner@example.com",
    "login": "owner",
    "username": "owner",
    "password": "StrongPass123!",
    "roles": ["super_admin"]
  }
]
```

Если `roles` не указан, используется `["super_admin"]`.

#### 5.2 Добавление/изменение role-permission маппинга

Используй шаблон `migrations/templates/roles_permissions_template.py`:

1. создай ревизию
   - `uv run alembic revision -m "rbac update"`
2. скопируй шаблон в новую ревизию
3. заполни обязательные данные:
   - `revision`, `down_revision`
   - `NEW_ROLES: dict[str, frozenset[str]]`
4. опционально заполни:
   - `SUPER_ADMIN_EXTRA_PERMISSIONS`
   - `ROLE_DESCRIPTIONS`
   - `ROLE_USER_BINDINGS` (роль -> tuple логинов пользователей)
5. применяй:
   - `uv run alembic upgrade head`

Что делает шаблон:

- валидирует формат role/permission кодов
- требует непустой набор прав для каждой объявленной роли
- делает upsert ролей и permission’ов
- синхронизирует связи role-permission (добавляет недостающие, удаляет лишние)
- может привязать существующих пользователей к ролям по login
- идемпотентен: повторный `upgrade` сохраняет целевое состояние
- `downgrade` удаляет только роли, объявленные в payload этой миграции

### 6) Конфигурация окружения

Создай свой `.env` из `.env.example` и заполни реальными значениями:

```bash
cp .env.example .env
```

Ключевые переменные:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_ALG`
- `JWT_SECRET`
- `JWT_ACCESS_TTL_S`
- `JWT_REFRESH_TTL_S`
- `DEFAULT_REGISTRATION_ROLE_CODE`
- `AUTH_USER_CACHE_TTL_S`
- настройки refresh-lock:
  - `REFRESH_LOCK_TTL_S`
  - `REFRESH_LOCK_WAIT_TIMEOUT_S`
- настройки пула/таймаутов:
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
  - `DB_POOL_TIMEOUT_S`
  - `DB_POOL_RECYCLE_S`
  - `DB_CONNECT_TIMEOUT_S`
- настройки Argon2:
  - `ARGON2_TIME_COST`
  - `ARGON2_MEMORY_COST_KIB`
  - `ARGON2_PARALLELISM`
  - `ARGON2_HASH_LEN`
  - `ARGON2_SALT_LEN`
- настройки observability (`OBS_OTEL_*`):
  - `OBS_OTEL_ENABLED`
  - `OBS_OTEL_SERVICE_NAME`
  - `OBS_OTEL_SERVICE_VERSION`
  - `OBS_OTEL_ENVIRONMENT`
  - `OBS_OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OBS_OTEL_METRICS_EXPORT_INTERVAL_MS`
  - `OBS_OTEL_HTTP_INSTRUMENTATION_ENABLED`
  - `OBS_OTEL_CAPTURE_REQUEST_HEADERS`
  - `OBS_OTEL_CAPTURE_RESPONSE_HEADERS`
  - `OBS_OTEL_SANITIZE_FIELDS_CSV`
- runtime-настройки observability:
  - `OBS_OTEL_GRPC_PORT`
  - `OBS_PROMETHEUS_PORT`
  - `OBS_GRAFANA_PORT`
  - `OBS_ALERTMANAGER_PORT`
  - `OBS_LOKI_PORT`
  - `OBS_ALLOY_PORT`
  - `OBS_TEMPO_HTTP_PORT`
  - `OBS_LOKI_RETENTION_PERIOD`

Для прода:

- используй сильные секреты и реальные креды
- не коммить `.env`
- в `APP_ENV=prod|production` отключаются docs/openapi

### 7) Запуск runtime

Compose scope-файлы (модульный runtime):

- `compose/data.yaml` — Postgres + Redis
- `compose/migrate.yaml` — one-shot шаг миграций/инициализации
- `compose/app.yaml` — app + nginx
- `compose/release.yaml` — release overlay (только pull image, без build)
- `compose/obs.yaml` — OTel/Prometheus/Grafana/Loki/Tempo/Alertmanager/VictoriaMetrics
- `compose/core.hostnet.yaml` — Linux host-network override для Postgres/Redis
- `compose/migrate.hostnet.yaml` — Linux host-network override для migrate
- `compose/app.hostnet.yaml` — Linux host-network override для app/nginx
- `compose/obs.hostnet.yaml` — Linux host-network override для observability

Базовый runtime (data + migrate + app):

```bash
docker compose -f compose/data.yaml down -v --remove-orphans
docker compose -f compose/data.yaml up -d
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/app.yaml up -d --build
```

Release runtime (prebuilt image, без сборки на сервере):

```bash
export APP_IMAGE=ghcr.io/<owner>/fastapi-template-app:vX.Y.Z
export MIGRATE_IMAGE=ghcr.io/<owner>/fastapi-template-migrate:vX.Y.Z
export NGINX_IMAGE=ghcr.io/<owner>/fastapi-template-nginx:vX.Y.Z
# Опционально для локального smoke с локальными тегами:
# export RELEASE_PULL_POLICY=missing

docker compose -f compose/data.yaml up -d
docker compose -f compose/data.yaml -f compose/migrate.yaml -f compose/release.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/release.yaml up -d
```

Runtime с observability:

```bash
OBS_OTEL_ENABLED=true docker compose -f compose/data.yaml -f compose/app.yaml -f compose/obs.yaml up -d --build
```

Linux host-network fallback (используй, если с хоста недоступны Docker-публикации портов):

```bash
docker compose -f compose/data.yaml -f compose/core.hostnet.yaml down -v --remove-orphans
docker compose -f compose/data.yaml up -d
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml -f compose/core.hostnet.yaml -f compose/migrate.hostnet.yaml run --rm migrate
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/app.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml up -d --build
OBS_OTEL_ENABLED=true docker compose -f compose/data.yaml -f compose/app.yaml -f compose/obs.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml -f compose/obs.hostnet.yaml up -d
```

Если `curl` на хосте возвращает `000` (`Empty reply from server`):

1. Обычно это сетевой/runtime нюанс Docker на конкретной машине, а не падение приложения.
2. Сначала проверь сервис из Docker-сети:

```bash
docker run --rm --network <project>_default curlimages/curl:8.12.1 -s -o /dev/null -w '%{http_code}\n' http://nginx:8080/system
```

3. Для этой машины используй host-network fallback:

```bash
docker compose -f compose/data.yaml -f compose/app.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml up -d --build
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/system
```

Стандартные порты сервисов:

- app: `8080`
- postgres: `5432`
- redis: `6379`
- OTel gRPC: `4317` (с `compose/obs.yaml`)
- Prometheus-1: `9090` (с `compose/obs.yaml`)
- Prometheus-2: `9091` (с `compose/obs.yaml`)
- Grafana: `3000` (с `compose/obs.yaml`)
- Alertmanager-1: `9093` (с `compose/obs.yaml`)
- Alertmanager-2: `9193` (с `compose/obs.yaml`)
- Loki: `3100` (с `compose/obs.yaml`)
- Alloy: `12345` (с `compose/obs.yaml`)
- Tempo: `3200` (с `compose/obs.yaml`)
- VictoriaMetrics: `8428` (с `compose/obs.yaml`)

Если любой стандартный порт занят, освободи его вручную до запуска (или останови конфликтующий процесс/контейнер).

Лимиты auth в nginx настраиваются через compose env:

- `AUTH_LOGIN_RATE`
- `AUTH_REGISTER_RATE`
- `AUTH_REFRESH_RATE`

Entrypoint’ы runtime:

- `compose/migrate.yaml` (`migrate.command`) -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `compose/app.yaml` (`app.command`) -> `uv run --no-dev --no-sync --frozen uvicorn ...`
- `compose/release.yaml` -> image-only сервисы app/migrate/nginx с `pull_policy: ${RELEASE_PULL_POLICY:-always}` (release-деплой без локальной сборки)

Горизонтальное масштабирование только app-сервиса (без затрагивания data/obs scope):

```bash
docker compose -f compose/data.yaml -f compose/app.yaml up -d --scale app=3
```

Observability-стек (включается добавлением `-f compose/obs.yaml` и `OBS_OTEL_ENABLED=true` для app):

- конфиг OTel Collector: `ops/otel-collector/config.yaml`
- конфиг scrape для Prometheus: `ops/prometheus/prometheus.yml`, `ops/prometheus/prometheus-2.yml`
- правила Prometheus: `ops/prometheus/rules/recording.yml`, `ops/prometheus/rules/alerts.yml`
- шаблон конфига Alertmanager: `ops/alertmanager/alertmanager.yml`
- скрипт рендера runtime-конфига Alertmanager: `ops/alertmanager/render-config.sh`
- конфиг Loki: `ops/loki/loki.yml`
- конфиг Alloy: `ops/alloy/config.alloy`
- конфиг Tempo: `ops/tempo/tempo.yml`
- provisioning datasource для Grafana: `ops/grafana/provisioning/datasources/datasources.yml`
- provisioning dashboard для Grafana: `ops/grafana/provisioning/dashboards/dashboards.yml`
- в compose OTEL по умолчанию выключен (`OBS_OTEL_ENABLED=false`)
- observability-порты в default compose-режиме биндуются только на localhost (`127.0.0.1`)
- gRPC Collector публикуется на `${OBS_OTEL_GRPC_PORT}` (по умолчанию `4317`) для локальной отладки
- UI Prometheus-1: `http://127.0.0.1:${OBS_PROMETHEUS_PORT}` (по умолчанию `9090`)
- UI Prometheus-2: `http://127.0.0.1:${OBS_PROMETHEUS_REPLICA_PORT}` (по умолчанию `9091`)
- UI Grafana: `http://127.0.0.1:${OBS_GRAFANA_PORT}` (по умолчанию `3000`, креды `admin/admin`; переопределяется через `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- UI Alertmanager-1: `http://127.0.0.1:${OBS_ALERTMANAGER_PORT}` (по умолчанию `9093`)
- UI Alertmanager-2: `http://127.0.0.1:${OBS_ALERTMANAGER_REPLICA_PORT}` (по умолчанию `9193`)
- API Loki: `http://127.0.0.1:${OBS_LOKI_PORT}` (по умолчанию `3100`)
- UI Alloy: `http://127.0.0.1:${OBS_ALLOY_PORT}` (по умолчанию `12345`)
- UI/API Tempo: `http://127.0.0.1:${OBS_TEMPO_HTTP_PORT}` (по умолчанию `3200`)
- UI/API VictoriaMetrics: `http://127.0.0.1:${OBS_VICTORIAMETRICS_PORT}` (по умолчанию `8428`)
- retention Prometheus задается через `OBS_PROMETHEUS_RETENTION` (по умолчанию `24h`) и хранится в Docker volume
- retention Alertmanager задается через `ALERTMANAGER_RETENTION` (по умолчанию `120h`) и хранится в Docker volume
- заголовок `X-Trace-Id` добавляется только при наличии валидного активного trace
- OTLP receiver в Collector защищен bearer auth (`OBS_OTEL_AUTH_TOKEN` в collector, `OBS_OTEL_EXPORTER_OTLP_HEADERS` в app)
- OTLP exporter в app поддерживает опциональные TLS/mTLS-файлы:
  - `OBS_OTEL_EXPORTER_OTLP_CA_CERT_FILE`
  - `OBS_OTEL_EXPORTER_OTLP_CLIENT_CERT_FILE`
  - `OBS_OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE`
- Опциональные флаги runtime-инструментации:
  - `OBS_OTEL_SQLALCHEMY_INSTRUMENTATION_ENABLED=true` включает инструментирование SQLAlchemy engine при создании
  - `OBS_OTEL_REDIS_INSTRUMENTATION_ENABLED=true` включает инструментирование Redis-клиента
- Collector строит span-to-metrics для зависимостей (DB/Redis) через `spanmetrics` connector:
  - Spanmetrics считаются в отдельном traces-pipeline без tail sampling; tail sampling применяется только в pipeline экспорта в Tempo.
  - `traces_spanmetrics_calls_total`
  - `traces_spanmetrics_duration_seconds_bucket`
- datasource Grafana конфигурируются через env:
  - `GRAFANA_PROMETHEUS_URL`
  - `GRAFANA_PROMETHEUS_LTS_URL`
  - `GRAFANA_LOKI_URL`
  - `GRAFANA_TEMPO_URL`
- Реплики Prometheus пишут remote_write в VictoriaMetrics для long-term retention (`/api/v1/write`)
- webhook endpoints Alertmanager конфигурируются через env:
  - `ALERTMANAGER_WEBHOOK_TICKET_URL`
  - `ALERTMANAGER_WEBHOOK_PAGE_URL`
  - `ALERTMANAGER_WEBHOOK_HEARTBEAT_URL`
- Опциональные прямые каналы (дополнительно к webhook):
  - `ALERTMANAGER_TICKET_SLACK_WEBHOOK_URL`
  - `ALERTMANAGER_PAGE_SLACK_WEBHOOK_URL`
  - `ALERTMANAGER_PAGE_PAGERDUTY_ROUTING_KEY`
- при `APP_ENV=prod` до запуска задай не-дефолтный `GRAFANA_ADMIN_PASSWORD` и не используй локальные URL для Alertmanager receiver-ов.

Для ежедневной работы в Prometheus добавлены shortcut recording series:

- `service:rps:5m`
- `service:error_rate_5xx:5m`
- `service:latency_p95_ms:5m`
- `dependency:db_redis_error_rate_pct:5m`
- `dependency:db_redis_latency_p95_seconds:5m`
- Также добавлены monitoring-of-monitoring alert-правила:
  - `NoHTTPMetricsData`, `NoCollectorMetricsData`, `Watchdog`
  - `CollectorExporterQueueSaturation`
  - `CollectorReceiverRefusedData`
  - `CollectorExporterSendFailures`
  - `AlertmanagerNotificationFailures`
- Alert-правила зависимостей:
  - `HighDependencyErrorRate`
  - `HighDependencyP95Latency`
- Уведомление по алерту отправляется только когда правило находится в firing не меньше времени `for`.

Преднастроенные Grafana dashboard:

- `Service RED`
- `Platform Observability`
- `Service RED` включает фильтры `Service`/`Dependency`, drill-down ссылки на dependency-alerts и ссылки в Tempo Explore.
- `Start Here (Overview)` преднастроен как домашний dashboard Grafana и показывает только базовые сигналы здоровья.

### 8) Актуальный API surface

Текущие пути OpenAPI:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /system`
- `POST /users`
- `GET /users/me`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /rbac/users/{user_id}/roles`
- `POST /rbac/users/{user_id}/roles`
- `DELETE /rbac/users/{user_id}/roles/{role_code}`

### 9) Smoke-проверка

```bash
curl -i http://127.0.0.1:8080/system
curl -i http://127.0.0.1:8080/openapi.json
curl -i http://127.0.0.1:8080/docs
```

### 10) Quality и тесты

Полный gate:

```bash
make check
```

Live endpoint matrix (опционально):

```bash
RUN_LIVE_E2E=1 E2E_BASE_URL=http://127.0.0.1:8080 uv run pytest tests/test_e2e_endpoint_matrix_live.py -q
```

Опциональный admin-сегмент:

```bash
E2E_ADMIN_BEARER="<admin access token>"
```
