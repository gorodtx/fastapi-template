# FastAPI Clean/DDD Template

[English](#english) | [Русский](#русский)

Production-oriented backend template: FastAPI + Clean/DDD + SQLAlchemy + Postgres + Redis + Alembic + JWT.

## Quick Deploy / Быстрый запуск

1. Create env file from template:
   - `cp .env.example .env`
2. Start services:
   - `docker compose up -d --build postgres redis migrate app nginx`
3. Run smoke checks:
   - `curl -i http://127.0.0.1:8080/system`
   - `curl -i http://127.0.0.1:8080/openapi.json`
   - `curl -i http://127.0.0.1:8080/docs`

## Technology Stack / Стек технологий

### Runtime

- `FastAPI`
- `Pydantic`
- `Uvicorn`
- `Dishka`
- `PostgreSQL`
- `SQLAlchemy`
- `asyncpg`
- `Alembic`
- `Redis`
- `Nginx`
- `Docker`
- `Docker Compose`
- `PyJWT`
- `argon2-cffi`
- `msgspec`
- `environs`

### Tooling & Quality

- `uv`
- `Ruff`
- `ty`
- `Pytest`
- `GitHub Actions`
- `make check`
- `Live E2E matrix`
- `GitHub Releases`

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
- Write use-cases run in short transactions (`run_in_tx` + `manager.transaction()`).
- Nested behavior is explicit:
  - `nested=True` -> savepoint (`begin_nested`)
  - already-inside scope -> no extra scope (`nullcontext`)
  - existing DB transaction without scope -> controlled commit/rollback scope
- Startup behavior:
  - app factory calls `register_domain_converters()` before wiring routes
  - converter/mapping registration is startup initialization
  - DB transactions are applied to write use-cases, not to converter registration

### 3) RBAC contract: fixed role/permission catalog

Role/permission **catalog** is fixed and versioned through migrations.  
Public API does **not** create roles or permissions; API only assigns/revokes roles for users.

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
- pool/timeout settings:
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
  - `DB_POOL_TIMEOUT_S`
  - `DB_POOL_RECYCLE_S`
  - `DB_CONNECT_TIMEOUT_S`

Production notes:

- use strong secrets and real credentials
- keep `.env` out of git
- docs/openapi are disabled when `APP_ENV` is `prod` or `production`

### 7) Runtime

Default runtime (cross-platform path):

```bash
docker compose down -v --remove-orphans
docker compose up -d --build postgres redis migrate app nginx
```

Linux fallback (for environments where bridge+ports is broken):

```bash
docker compose down -v --remove-orphans
docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

If Docker build has DNS issues with PyPI:

```bash
DOCKER_BUILD_NETWORK=host docker compose up -d --build postgres redis migrate app nginx
DOCKER_BUILD_NETWORK=host docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

Runtime entrypoints:

- `nginx/migrate-up.sh` -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `nginx/app-up.sh` -> `uv run --no-dev --no-sync --frozen uvicorn ...`

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
- Write use-case выполняются в короткой транзакции (`run_in_tx` + `manager.transaction()`).
- Поведение вложенности:
  - `nested=True` -> savepoint (`begin_nested`)
  - если scope уже открыт -> без доп. scope (`nullcontext`)
  - если внешняя транзакция уже есть, но scope нет -> контролируемый commit/rollback scope
- Поведение старта:
  - в фабрике приложения вызывается `register_domain_converters()`
  - регистрация converter/mapping-объектов делается на старте
  - транзакции БД применяются к write use-case, а не к регистрации конвертеров

### 3) RBAC-контракт: фиксированный каталог ролей/прав

Каталог ролей/прав фиксирован и версионируется миграциями.  
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
- настройки пула/таймаутов:
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
  - `DB_POOL_TIMEOUT_S`
  - `DB_POOL_RECYCLE_S`
  - `DB_CONNECT_TIMEOUT_S`

Для прода:

- используй сильные секреты и реальные креды
- не коммить `.env`
- в `APP_ENV=prod|production` отключаются docs/openapi

### 7) Запуск runtime

Базовый запуск (кроссплатформенный путь):

```bash
docker compose down -v --remove-orphans
docker compose up -d --build postgres redis migrate app nginx
```

Linux fallback (если в окружении ломается bridge+ports):

```bash
docker compose down -v --remove-orphans
docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

Если в Docker build проблемы DNS с PyPI:

```bash
DOCKER_BUILD_NETWORK=host docker compose up -d --build postgres redis migrate app nginx
DOCKER_BUILD_NETWORK=host docker compose -f compose.yaml -f compose.linux-hostnet.yaml up -d --build postgres redis migrate app nginx
```

Entrypoint’ы runtime:

- `nginx/migrate-up.sh` -> `uv run --no-dev --no-sync --frozen alembic upgrade head`
- `nginx/app-up.sh` -> `uv run --no-dev --no-sync --frozen uvicorn ...`

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
