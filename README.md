# FastAPI Clean/DDD Template

[English](#english) | [Русский](#русский)

Production-oriented backend template: FastAPI + Clean/DDD + SQLAlchemy + Postgres + Redis + Alembic + JWT.

## Quick Deploy / Быстрый запуск

Release / Релиз: <https://github.com/gorodtx/fastapi-template/releases/latest>

Use release tag (например `v1.0.0`) and run one command:

```bash
TAG=v1.0.0 && git clone --depth 1 --branch "$TAG" https://github.com/gorodtx/fastapi-template.git && cd fastapi-template && cp .env.example .env && docker compose up -d --build postgres redis migrate app nginx
```

What to use from release / Что использовать из релиза:

- clone by semantic tag (`git clone --branch vX.Y.Z`) as the single install path / клон по тегу — единый путь установки
- `.env.example` -> `.env` with real credentials before first start / реальные значения перед стартом
- runtime files from tag: `compose.yaml`, `nginx/`, `migrations/`, `alembic.ini`, `src/`

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
- Nested behavior is explicit:
  - `nested=True` -> savepoint (`begin_nested`)
  - already-inside scope -> no extra scope (`nullcontext`)
  - existing DB transaction without scope -> controlled commit/rollback scope
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

Production notes:

- use strong secrets and real credentials
- keep `.env` out of git
- docs/openapi are disabled when `APP_ENV` is `prod` or `production`

### 7) Runtime

Recommended local start (includes Linux host-network fallback logic, core profile by default):

```bash
./scripts/up.sh
```

Enable observability profile on demand:

```bash
ENABLE_OBSERVABILITY=1 ./scripts/up.sh
```

`./scripts/up.sh` always enforces standard service ports:

- app: `8080`
- postgres: `5432`
- redis: `6379`
- OTel gRPC: `4317` (when observability is enabled)
- Prometheus: `9090` (when observability is enabled)
- Grafana: `3000` (when observability is enabled)

If any required port is occupied, the script automatically tries to free it:
- first tears down containers from the current compose project (idempotent restart path)
- then stops Docker containers publishing this port
- then terminates remaining local listener processes

On Linux, if default bridge mode is healthy only from inside the compose network but not from host URLs, the script auto-switches to host-network fallback to restore host URL reachability.
In this fallback mode, core services and observability services run on host networking, so default URLs stay reachable (`:8080`, `:9090`, `:3000`).
For Prometheus in host-network fallback, scrape target switches to `127.0.0.1:9464` (instead of `otel-collector:9464`).

Default runtime (cross-platform path):

```bash
docker compose down -v --remove-orphans
docker compose up -d --build postgres redis migrate app nginx
```

If Docker build has DNS issues with PyPI:

```bash
DOCKER_BUILD_NETWORK=host docker compose up -d --build postgres redis migrate app nginx
```

Core + observability (manual compose path):

```bash
docker compose --profile obs up -d --build postgres redis otel-collector migrate app nginx prometheus grafana
```

Nginx auth rate limits are configurable via compose env vars:

- `AUTH_LOGIN_RATE`
- `AUTH_REGISTER_RATE`
- `AUTH_REFRESH_RATE`

Runtime entrypoints:

- `nginx/migrate-up.sh` -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `nginx/app-up.sh` -> `uv run --no-dev --no-sync --frozen uvicorn ...`

Observability stack (enabled via `ENABLE_OBSERVABILITY=1 ./scripts/up.sh` or `--profile obs`):

- OTel Collector config: `ops/otel-collector/config.yaml`
- Prometheus scrape config: `ops/prometheus/prometheus.yml`
- App OTEL is disabled by default in compose (`OBS_OTEL_ENABLED=false`) and auto-enabled by `./scripts/up.sh` when observability is requested
- Collector gRPC is exposed via `${OBS_OTEL_GRPC_PORT}` (default `4317`) for Linux host-network fallback path
- Prometheus UI: `http://127.0.0.1:${OBS_PROMETHEUS_PORT}` (default `9090`)
- Grafana UI: `http://127.0.0.1:${OBS_GRAFANA_PORT}` (default `3000`, credentials `admin/admin`; override via `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- `X-Trace-Id` response header is emitted only when a valid active trace exists

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
- Поведение вложенности:
  - `nested=True` -> savepoint (`begin_nested`)
  - если scope уже открыт -> без доп. scope (`nullcontext`)
  - если внешняя транзакция уже есть, но scope нет -> контролируемый commit/rollback scope
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

Для прода:

- используй сильные секреты и реальные креды
- не коммить `.env`
- в `APP_ENV=prod|production` отключаются docs/openapi

### 7) Запуск runtime

Рекомендуемый локальный запуск (включает Linux host-network fallback, по умолчанию профиль core):

```bash
./scripts/up.sh
```

Включение observability-профиля:

```bash
ENABLE_OBSERVABILITY=1 ./scripts/up.sh
```

`./scripts/up.sh` всегда использует стандартные порты сервисов:

- app: `8080`
- postgres: `5432`
- redis: `6379`
- OTel gRPC: `4317` (при включенном observability)
- Prometheus: `9090` (при включенном observability)
- Grafana: `3000` (при включенном observability)

Если любой обязательный порт занят, скрипт автоматически пытается его освободить:
- сначала останавливает контейнеры текущего compose-проекта (идемпотентный restart path)
- затем останавливает Docker-контейнеры, публикующие этот порт
- затем завершает оставшиеся локальные процессы, слушающие порт

На Linux, если дефолтный bridge-режим работает только внутри docker-сети, но host URL недоступны, скрипт автоматически переключается на host-network fallback, чтобы URL с хоста открывались.
В этом fallback-режиме и core, и observability сервисы запускаются в host networking, поэтому стандартные URL остаются доступны (`:8080`, `:9090`, `:3000`).
Для Prometheus в host-network fallback scrape target переключается на `127.0.0.1:9464` (вместо `otel-collector:9464`).

Базовый запуск (кроссплатформенный путь):

```bash
docker compose down -v --remove-orphans
docker compose up -d --build postgres redis migrate app nginx
```

Если в Docker build проблемы DNS с PyPI:

```bash
DOCKER_BUILD_NETWORK=host docker compose up -d --build postgres redis migrate app nginx
```

Core + observability (ручной compose-путь):

```bash
docker compose --profile obs up -d --build postgres redis otel-collector migrate app nginx prometheus grafana
```

Лимиты auth в nginx настраиваются через compose env:

- `AUTH_LOGIN_RATE`
- `AUTH_REGISTER_RATE`
- `AUTH_REFRESH_RATE`

Entrypoint’ы runtime:

- `nginx/migrate-up.sh` -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `nginx/app-up.sh` -> `uv run --no-dev --no-sync --frozen uvicorn ...`

Observability-стек (включается через `ENABLE_OBSERVABILITY=1 ./scripts/up.sh` или `--profile obs`):

- конфиг OTel Collector: `ops/otel-collector/config.yaml`
- конфиг scrape для Prometheus: `ops/prometheus/prometheus.yml`
- в compose OTEL по умолчанию выключен (`OBS_OTEL_ENABLED=false`), а `./scripts/up.sh` включает его автоматически при включенном observability-профиле
- gRPC Collector публикуется на `${OBS_OTEL_GRPC_PORT}` (по умолчанию `4317`) для Linux host-network fallback сценария
- UI Prometheus: `http://127.0.0.1:${OBS_PROMETHEUS_PORT}` (по умолчанию `9090`)
- UI Grafana: `http://127.0.0.1:${OBS_GRAFANA_PORT}` (по умолчанию `3000`, креды `admin/admin`; переопределяется через `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`)
- заголовок `X-Trace-Id` добавляется только при наличии валидного активного trace

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
