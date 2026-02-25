# Подробное руководство (Русский)

[Назад в README](../README.md)

## Содержание

- [1) Что даёт шаблон](#1-что-даёт-шаблон)
- [2) Архитектура и модель транзакций](#2-архитектура-и-модель-транзакций)
- [3) RBAC-контракт: версионируемый каталог ролей/прав](#3-rbac-контракт-версионируемый-каталог-ролейправ)
- [4) Схема БД и связи таблиц](#4-схема-бд-и-связи-таблиц)
- [5) Механизм RBAC-миграций (как менять роли/права)](#5-механизм-rbac-миграций-как-менять-ролиправа)
- [6) Конфигурация окружения](#6-конфигурация-окружения)
- [7) Запуск runtime](#7-запуск-runtime)
- [8) Актуальный API surface](#8-актуальный-api-surface)
- [9) Smoke-проверка](#9-smoke-проверка)
- [10) Quality и тесты](#10-quality-и-тесты)

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

CI release flow по тегу:

- `.github/workflows/release-images.yml` собирает и публикует образы `app/migrate/nginx` в GHCR на тегах `v*`.
- `.github/workflows/release.yml` автоматически создаёт GitHub Release object для того же тега.

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
