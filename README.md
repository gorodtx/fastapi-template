# FastAPI Clean/DDD Template

[English](#english) | [Русский](#русский)

Production-oriented backend template: FastAPI + Clean/DDD + SQLAlchemy + Postgres + Redis + Alembic + JWT.

[![GitHub Actions CI](https://github.com/gorodtx/fastapi-template/actions/workflows/ci.yml/badge.svg)](https://github.com/gorodtx/fastapi-template/actions/workflows/ci.yml)
[![GitHub Release](https://img.shields.io/github/v/release/gorodtx/fastapi-template)](https://github.com/gorodtx/fastapi-template/releases/latest)
[![make check required](https://img.shields.io/badge/make%20check-required-2ea44f)](#quality-gates--контроль-качества)

## Contents / Содержание

- [Quick Start](#quick-start--быстрый-старт)
- [Technology Stack](#technology-stack--стек-технологий)
- [Navigation by Task](#navigation-by-task--навигация-по-задачам)
- [Compose Scopes](#compose-scopes--скоупы-compose)
- [Release and CI](#release-and-ci--релиз-и-ci)
- [Detailed Guides](#detailed-guides--подробные-руководства)
- [Smoke Checks](#smoke-checks--быстрые-проверки)
- [Quality Gates](#quality-gates--контроль-качества)
- [Q&A](#qa)

## Quick Start / Быстрый старт

Release / Релиз: <https://github.com/gorodtx/fastapi-template/releases/latest>

### Option A: Local build / Локальная сборка

```bash
cp .env.example .env
docker compose -f compose/data.yaml up -d
DOCKER_BUILD_NETWORK=host docker compose -f compose/data.yaml -f compose/migrate.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/app.yaml up -d --build
```

### Option B: Release images (no server build) / Релизные образы (без сборки)

```bash
export APP_IMAGE=ghcr.io/<owner>/fastapi-template-app:vX.Y.Z
export MIGRATE_IMAGE=ghcr.io/<owner>/fastapi-template-migrate:vX.Y.Z
export NGINX_IMAGE=ghcr.io/<owner>/fastapi-template-nginx:vX.Y.Z

docker compose -f compose/data.yaml up -d
docker compose -f compose/data.yaml -f compose/migrate.yaml -f compose/release.yaml run --rm migrate
docker compose -f compose/data.yaml -f compose/release.yaml up -d
```

### Option C: Core + Observability / Core + Observability

```bash
docker compose -f compose/data.yaml -f compose/app.yaml -f compose/obs.yaml up -d --build
```

`compose/obs.yaml` (и `compose/obs.hostnet.yaml`) автоматически включает
`OBS_OTEL_ENABLED=true` для `app`, чтобы метрики/трейсы начинали поступать
сразу после поднятия observability-скоупа.

## Technology Stack / Стек технологий

### Runtime

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?logo=uvicorn&logoColor=white)](https://www.uvicorn.org/)
[![Dishka](https://img.shields.io/badge/Dishka-DI-4B5563)](https://github.com/reagento/dishka)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PgBouncer](https://img.shields.io/badge/PgBouncer-connection%20pooling-2563EB)](https://www.pgbouncer.org/)
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
[![GitHub Release](https://img.shields.io/github/v/release/gorodtx/fastapi-template)](https://github.com/gorodtx/fastapi-template/releases/latest)
[![make check required](https://img.shields.io/badge/make%20check-required-2ea44f)](#quality-gates--контроль-качества)

## Navigation by Task / Навигация по задачам

| Task / Задача | Go to / Ссылка |
| --- | --- |
| Architecture, layers, transaction model | [`docs/guide.en.md`](docs/guide.en.md#2-architecture-and-transaction-model) |
| Архитектура, слои, транзакции | [`docs/guide.ru.md`](docs/guide.ru.md#2-архитектура-и-модель-транзакций) |
| RBAC contract + migrations | [`docs/guide.en.md`](docs/guide.en.md#3-rbac-contract-versioned-rolepermission-catalog) |
| RBAC-контракт + миграции | [`docs/guide.ru.md`](docs/guide.ru.md#3-rbac-контракт-версионируемый-каталог-ролейправ) |
| Environment variables | [`docs/guide.en.md`](docs/guide.en.md#6-environment-setup) |
| Переменные окружения | [`docs/guide.ru.md`](docs/guide.ru.md#6-конфигурация-окружения) |
| Runtime/compose commands | [`docs/guide.en.md`](docs/guide.en.md#7-runtime) |
| Команды запуска/compose | [`docs/guide.ru.md`](docs/guide.ru.md#7-запуск-runtime) |
| Observability details | [`docs/guide.en.md`](docs/guide.en.md#7-runtime) / [`docs/guide.ru.md`](docs/guide.ru.md#7-запуск-runtime) |
| API surface and smoke | [`docs/guide.en.md`](docs/guide.en.md#8-api-surface-current) / [`docs/guide.ru.md`](docs/guide.ru.md#8-актуальный-api-surface) |

## Compose Scopes / Скоупы compose

- `compose/data.yaml` -> Postgres + PgBouncer + Redis
- `compose/migrate.yaml` -> one-shot migrations/bootstrap
- `compose/app.yaml` -> app + nginx (build path)
- `compose/release.yaml` -> app + migrate + nginx (image-only path)
- `compose/obs.yaml` -> OTel/Prometheus/Grafana/Loki/Tempo(distributed)/Alertmanager/VictoriaMetrics
- `compose/core.hostnet.yaml`, `compose/app.hostnet.yaml`, `compose/migrate.hostnet.yaml`, `compose/obs.hostnet.yaml` -> Linux host-network fallback
- `compose/obs.hostnet.yaml` uses a hostnet-specific Grafana provisioning set (Prometheus/Loki only). Tempo datasource and Tempo scrape are intentionally disabled in hostnet mode to avoid false `down`/`EOF` states on this runtime path; full trace UI is available in standard `compose/obs.yaml`.

Observability log flow:
- app logs -> OTLP gRPC -> OTel Collector -> Loki
- container logs -> Alloy `loki.source.docker` (Docker API) -> Loki

Tempo distributed topology in `compose/obs.yaml`:
- `tempo-distributor` (OTLP ingest)
- `tempo-ingester`
- `tempo-querier`
- `tempo-query-frontend` (Grafana datasource endpoint)
- `tempo-compactor` (`backend-scheduler` target)
- `tempo-metrics-generator` (span-metrics + service-graphs)

Object storage for traces:
- Local default: MinIO (`minio` + `minio-init` bucket bootstrap)
- Production: set `TEMPO_S3_*` to external S3-compatible storage

DB observability in `compose/obs.yaml`:
- `postgres-exporter` (`:9187`) for Postgres saturation/locks/temp/deadlocks metrics
- `pgbouncer-exporter` (`:9127`) for PgBouncer queue/maxwait/saturation metrics
- Grafana dashboard: `Postgres Saturation`
- Grafana dashboard: `PgBouncer Saturation`
- Prometheus rules/alerts: `db:postgres_*`, `db:pgbouncer_*`, `PostgresConnectionsSaturation`, `PostgresDeadlocksDetected`, `PostgresTempBytesSpike`, `PgBouncerConnectionsSaturation`, `PgBouncerClientQueueWaiting`, `PgBouncerClientMaxwaitHigh`

## Release and CI / Релиз и CI

- `.github/workflows/ci.yml` -> lint/format/type/tests
- `.github/workflows/release-images.yml` -> builds and publishes `app/migrate/nginx` to GHCR on `v*` tags
- `.github/workflows/release.yml` -> creates GitHub Release object automatically on `v*` tags

Recommended release flow / Рекомендуемый релизный поток:

```bash
git checkout prod
git pull
git tag vX.Y.Z
git push origin prod
git push origin vX.Y.Z
```

## Detailed Guides / Подробные руководства

- Full English guide: [`docs/guide.en.md`](docs/guide.en.md)
- Полное руководство на русском: [`docs/guide.ru.md`](docs/guide.ru.md)

These guides include full runtime matrix, env catalog, observability details, RBAC migration procedure, API list, and quality commands.

## Smoke Checks / Быстрые проверки

```bash
curl -i http://127.0.0.1:8080/system
curl -i http://127.0.0.1:8080/openapi.json
curl -i http://127.0.0.1:8080/docs
```

## Quality Gates / Контроль качества

```bash
make check
```

Optional live matrix / Опциональная живая матрица:

```bash
RUN_LIVE_E2E=1 E2E_BASE_URL=http://127.0.0.1:8080 uv run pytest tests/test_e2e_endpoint_matrix_live.py -q
```

## Q&A

### `curl` returns `000` from host / `curl` возвращает `000` с хоста

1. Verify container-network reachability first:

```bash
docker run --rm --network <project>_default curlimages/curl:8.12.1 -s -o /dev/null -w '%{http_code}\n' http://nginx:8080/system
```

2. If this is `200`, use host-network fallback on this machine:

```bash
docker compose -f compose/data.yaml -f compose/app.yaml -f compose/core.hostnet.yaml -f compose/app.hostnet.yaml up -d --build
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/system
```

### `OBS_OTEL_ENABLED=true` and app fails on startup

If startup error contains `opentelemetry-instrumentation-logging`, install this runtime package in your app image/environment. Logging correlation is configured as a hard requirement for observability mode.

### Live e2e matrix returns `429` via nginx

`tests/test_e2e_endpoint_matrix_live.py` has dense auth calls; nginx rate-limits can produce `429`.
For deterministic live matrix use app upstream directly:

```bash
RUN_LIVE_E2E=1 E2E_BASE_URL=http://127.0.0.1:8000 uv run pytest tests/test_e2e_endpoint_matrix_live.py -q
```

### Migration safety policy (expand/contract)

- Non-bootstrap migrations must use `postgresql_concurrently=True` for `op.create_index` / `op.drop_index`.
- Bootstrap-only exceptions must be documented in revision header with:
  `# migration-lint: allow-nonconcurrent-index`
- CI gate: `tests/test_migration_safety_gate.py`.
- Release checklist:
  1. `expand`: nullable/new columns, concurrent indexes, `NOT VALID` constraints.
  2. Backfill in controlled batches.
  3. Cutover application reads/writes.
  4. `contract`: drop legacy structures only after stabilization.

### DB connection routing / Маршрут DB-подключений

- `app` и `release app` по умолчанию подключаются к БД через PgBouncer:
  `postgresql+asyncpg://...@pgbouncer:5432/...`
- `migrate` подключается напрямую к `postgres`, чтобы DDL-миграции не зависели от режима pooler.
- Для asyncpg через PgBouncer включен `prepared_statement_cache_size=0` в дефолтном DSN.
- Для PgBouncer-DSN SQLAlchemy использует `NullPool` (без двойного pooling в приложении).
- Бюджет соединений валидируется на старте приложения:
  `APP_INSTANCE_COUNT * (DB_POOL_SIZE + DB_MAX_OVERFLOW) <= PGBOUNCER_MAX_CLIENT_CONN`,
  `PGBOUNCER_DEFAULT_POOL_SIZE + PGBOUNCER_RESERVE_POOL_SIZE <= PGBOUNCER_MAX_DB_CONNECTIONS`.
  Дополнительно при явной передаче `POSTGRES_MAX_CONNECTIONS` проверяется:
  `PGBOUNCER_MAX_DB_CONNECTIONS <= POSTGRES_MAX_CONNECTIONS - POSTGRES_SUPERUSER_RESERVED_CONNECTIONS`.
- PgBouncer hardening defaults:
  `PGBOUNCER_AUTH_TYPE=scram-sha-256`,
  host bind для `6432` только на `127.0.0.1`,
  pin image digest через `PGBOUNCER_IMAGE`.
- TLS для PgBouncer настраивается env-парами:
  `PGBOUNCER_CLIENT_TLS_SSLMODE`, `PGBOUNCER_SERVER_TLS_SSLMODE`
  (+ `*_KEY_FILE`, `*_CERT_FILE`, `*_CA_FILE` при необходимости).
- Redis guardrails задаются через:
  `REDIS_MAX_CONNECTIONS`, `REDIS_MAXMEMORY`, `REDIS_MAXMEMORY_POLICY`.

## thks :)

For complete technical details [`docs/guide.en.md`](docs/guide.en.md).
Все подробности - [`docs/guide.ru.md`](docs/guide.ru.md).
