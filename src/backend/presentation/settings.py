from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from environs import Env

_PGBOUNCER_DEFAULT_PORT = 6432


def _require_str(env: Env, name: str) -> str:
    value = env.str(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _require_int(env: Env, name: str) -> int:
    value = env.int(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _require_positive_int(value: int, name: str) -> int:
    if value <= 0:
        raise RuntimeError(
            f"Environment variable must be positive integer: {name}"
        )
    return value


def _require_non_negative_int(value: int, name: str) -> int:
    if value < 0:
        raise RuntimeError(
            f"Environment variable must be non-negative integer: {name}"
        )
    return value


def _require_positive_float(value: float, name: str) -> float:
    if value <= 0:
        raise RuntimeError(
            f"Environment variable must be positive number: {name}"
        )
    return value


def _optional_non_negative_int(env: Env, name: str) -> int | None:
    raw_value = env.str(name, default="")
    if raw_value is None or raw_value.strip() == "":
        return None
    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"Environment variable must be integer: {name}"
        ) from exc
    if parsed_value < 0:
        raise RuntimeError(
            f"Environment variable must be non-negative integer: {name}"
        )
    return parsed_value


def _is_pgbouncer_database_url(database_url: str) -> bool:
    parsed = urlparse(database_url)
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if "pgbouncer" in host:
        return True
    return port == _PGBOUNCER_DEFAULT_PORT


def _require_pgbouncer_database_url(app_env: str, database_url: str) -> str:
    normalized_env = app_env.lower()
    if normalized_env in {
        "dev",
        "prod",
        "production",
    } and not _is_pgbouncer_database_url(database_url):
        raise RuntimeError(
            "DATABASE_URL must point to PgBouncer in APP_ENV=dev/prod "
            "(host containing 'pgbouncer' or port 6432)"
        )
    return database_url


def _validate_connection_budget(
    *,
    app_instance_count: int,
    db_pool_size: int,
    db_max_overflow: int,
    pgbouncer_max_client_conn: int,
    pgbouncer_default_pool_size: int,
    pgbouncer_reserve_pool_size: int,
    pgbouncer_max_db_connections: int,
    postgres_max_connections: int | None,
    postgres_superuser_reserved_connections: int | None,
) -> None:
    total_client_demand = app_instance_count * (db_pool_size + db_max_overflow)
    if total_client_demand > pgbouncer_max_client_conn:
        raise RuntimeError(
            "Connection budget exceeded: "
            "APP_INSTANCE_COUNT * (DB_POOL_SIZE + DB_MAX_OVERFLOW) "
            "must be <= PGBOUNCER_MAX_CLIENT_CONN"
        )

    pgbouncer_server_budget = (
        pgbouncer_default_pool_size + pgbouncer_reserve_pool_size
    )
    if pgbouncer_server_budget > pgbouncer_max_db_connections:
        raise RuntimeError(
            "Invalid PgBouncer budget: "
            "PGBOUNCER_DEFAULT_POOL_SIZE + PGBOUNCER_RESERVE_POOL_SIZE "
            "must be <= PGBOUNCER_MAX_DB_CONNECTIONS"
        )

    if postgres_max_connections is not None:
        reserved_connections = postgres_superuser_reserved_connections or 0
        postgres_effective_budget = (
            postgres_max_connections - reserved_connections
        )
        if postgres_effective_budget <= 0:
            raise RuntimeError(
                "Invalid Postgres budget: "
                "POSTGRES_MAX_CONNECTIONS must be greater than "
                "POSTGRES_SUPERUSER_RESERVED_CONNECTIONS"
            )
        if pgbouncer_max_db_connections > postgres_effective_budget:
            raise RuntimeError(
                "PgBouncer DB budget exceeds Postgres capacity: "
                "PGBOUNCER_MAX_DB_CONNECTIONS must be <= "
                "POSTGRES_MAX_CONNECTIONS - "
                "POSTGRES_SUPERUSER_RESERVED_CONNECTIONS"
            )


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    database_url: str
    redis_url: str | None
    redis_max_connections: int
    default_registration_role_code: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout_s: int
    db_pool_recycle_s: int
    db_connect_timeout_s: int
    app_instance_count: int
    pgbouncer_max_client_conn: int
    pgbouncer_default_pool_size: int
    pgbouncer_reserve_pool_size: int
    pgbouncer_max_db_connections: int
    postgres_max_connections: int | None
    postgres_superuser_reserved_connections: int | None

    jwt_issuer: str
    jwt_audience: str
    jwt_alg: str
    jwt_secret: str
    jwt_access_ttl_s: int
    jwt_refresh_ttl_s: int
    auth_user_cache_ttl_s: int
    refresh_lock_ttl_s: float
    refresh_lock_wait_timeout_s: float
    argon2_time_cost: int
    argon2_memory_cost_kib: int
    argon2_parallelism: int
    argon2_hash_len: int
    argon2_salt_len: int
    obs_otel_enabled: bool
    obs_otel_service_name: str
    obs_otel_service_version: str
    obs_otel_environment: str
    obs_otel_exporter_otlp_endpoint: str | None
    obs_otel_exporter_otlp_headers: str | None
    obs_otel_exporter_otlp_ca_cert_file: str | None
    obs_otel_exporter_otlp_client_cert_file: str | None
    obs_otel_exporter_otlp_client_key_file: str | None
    obs_otel_metrics_export_interval_ms: int
    obs_otel_traces_sampler: str
    obs_otel_traces_sampler_arg: float
    obs_otel_http_instrumentation_enabled: bool
    obs_otel_sqlalchemy_instrumentation_enabled: bool
    obs_otel_redis_instrumentation_enabled: bool
    obs_otel_capture_request_headers: bool
    obs_otel_capture_response_headers: bool
    obs_otel_sanitize_fields_csv: str
    obs_otel_semconv_stability_opt_in: str | None

    @staticmethod
    def from_env(env: Env) -> Settings:
        app_env: str = env.str("APP_ENV", default="dev") or "dev"
        database_url = _require_pgbouncer_database_url(
            app_env,
            _require_str(env, "DATABASE_URL"),
        )
        db_pool_size = _require_positive_int(
            env.int("DB_POOL_SIZE", default=10),
            "DB_POOL_SIZE",
        )
        db_max_overflow = _require_non_negative_int(
            env.int("DB_MAX_OVERFLOW", default=20),
            "DB_MAX_OVERFLOW",
        )
        app_instance_count = _require_positive_int(
            env.int("APP_INSTANCE_COUNT", default=1),
            "APP_INSTANCE_COUNT",
        )
        pgbouncer_max_client_conn = _require_positive_int(
            env.int("PGBOUNCER_MAX_CLIENT_CONN", default=500),
            "PGBOUNCER_MAX_CLIENT_CONN",
        )
        pgbouncer_default_pool_size = _require_positive_int(
            env.int("PGBOUNCER_DEFAULT_POOL_SIZE", default=50),
            "PGBOUNCER_DEFAULT_POOL_SIZE",
        )
        pgbouncer_reserve_pool_size = _require_non_negative_int(
            env.int("PGBOUNCER_RESERVE_POOL_SIZE", default=10),
            "PGBOUNCER_RESERVE_POOL_SIZE",
        )
        pgbouncer_max_db_connections = _require_positive_int(
            env.int("PGBOUNCER_MAX_DB_CONNECTIONS", default=100),
            "PGBOUNCER_MAX_DB_CONNECTIONS",
        )
        postgres_max_connections = _optional_non_negative_int(
            env,
            "POSTGRES_MAX_CONNECTIONS",
        )
        postgres_superuser_reserved_connections = _optional_non_negative_int(
            env,
            "POSTGRES_SUPERUSER_RESERVED_CONNECTIONS",
        )
        _validate_connection_budget(
            app_instance_count=app_instance_count,
            db_pool_size=db_pool_size,
            db_max_overflow=db_max_overflow,
            pgbouncer_max_client_conn=pgbouncer_max_client_conn,
            pgbouncer_default_pool_size=pgbouncer_default_pool_size,
            pgbouncer_reserve_pool_size=pgbouncer_reserve_pool_size,
            pgbouncer_max_db_connections=pgbouncer_max_db_connections,
            postgres_max_connections=postgres_max_connections,
            postgres_superuser_reserved_connections=(
                postgres_superuser_reserved_connections
            ),
        )
        redis_url: str | None = env.str("REDIS_URL", default="") or None
        default_registration_role_code = (
            env.str("DEFAULT_REGISTRATION_ROLE_CODE", default="user") or "user"
        )
        obs_otel_enabled = env.bool("OBS_OTEL_ENABLED", default=False)
        obs_otel_exporter_otlp_endpoint = (
            env.str("OBS_OTEL_EXPORTER_OTLP_ENDPOINT", default="") or None
        )
        obs_otel_exporter_otlp_headers = (
            env.str("OBS_OTEL_EXPORTER_OTLP_HEADERS", default="") or None
        )
        obs_otel_exporter_otlp_ca_cert_file = (
            env.str("OBS_OTEL_EXPORTER_OTLP_CA_CERT_FILE", default="") or None
        )
        obs_otel_exporter_otlp_client_cert_file = (
            env.str("OBS_OTEL_EXPORTER_OTLP_CLIENT_CERT_FILE", default="")
            or None
        )
        obs_otel_exporter_otlp_client_key_file = (
            env.str("OBS_OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE", default="")
            or None
        )

        return Settings(
            app_env=app_env,
            database_url=database_url,
            redis_url=redis_url,
            redis_max_connections=_require_positive_int(
                env.int("REDIS_MAX_CONNECTIONS", default=100),
                "REDIS_MAX_CONNECTIONS",
            ),
            default_registration_role_code=default_registration_role_code,
            db_pool_size=db_pool_size,
            db_max_overflow=db_max_overflow,
            db_pool_timeout_s=env.int("DB_POOL_TIMEOUT_S", default=30),
            db_pool_recycle_s=env.int("DB_POOL_RECYCLE_S", default=1800),
            db_connect_timeout_s=env.int("DB_CONNECT_TIMEOUT_S", default=10),
            app_instance_count=app_instance_count,
            pgbouncer_max_client_conn=pgbouncer_max_client_conn,
            pgbouncer_default_pool_size=pgbouncer_default_pool_size,
            pgbouncer_reserve_pool_size=pgbouncer_reserve_pool_size,
            pgbouncer_max_db_connections=pgbouncer_max_db_connections,
            postgres_max_connections=postgres_max_connections,
            postgres_superuser_reserved_connections=(
                postgres_superuser_reserved_connections
            ),
            jwt_issuer=_require_str(env, "JWT_ISSUER"),
            jwt_audience=_require_str(env, "JWT_AUDIENCE"),
            jwt_alg=_require_str(env, "JWT_ALG"),
            jwt_secret=_require_str(env, "JWT_SECRET"),
            jwt_access_ttl_s=_require_positive_int(
                _require_int(env, "JWT_ACCESS_TTL_S"),
                "JWT_ACCESS_TTL_S",
            ),
            jwt_refresh_ttl_s=_require_positive_int(
                _require_int(env, "JWT_REFRESH_TTL_S"),
                "JWT_REFRESH_TTL_S",
            ),
            auth_user_cache_ttl_s=_require_positive_int(
                env.int("AUTH_USER_CACHE_TTL_S", default=300),
                "AUTH_USER_CACHE_TTL_S",
            ),
            refresh_lock_ttl_s=_require_positive_float(
                env.float("REFRESH_LOCK_TTL_S", default=10.0),
                "REFRESH_LOCK_TTL_S",
            ),
            refresh_lock_wait_timeout_s=_require_positive_float(
                env.float("REFRESH_LOCK_WAIT_TIMEOUT_S", default=1.0),
                "REFRESH_LOCK_WAIT_TIMEOUT_S",
            ),
            argon2_time_cost=env.int("ARGON2_TIME_COST", default=3),
            argon2_memory_cost_kib=env.int(
                "ARGON2_MEMORY_COST_KIB", default=65536
            ),
            argon2_parallelism=env.int("ARGON2_PARALLELISM", default=4),
            argon2_hash_len=env.int("ARGON2_HASH_LEN", default=32),
            argon2_salt_len=env.int("ARGON2_SALT_LEN", default=16),
            obs_otel_enabled=obs_otel_enabled,
            obs_otel_service_name=(
                env.str("OBS_OTEL_SERVICE_NAME", default="backend")
                or "backend"
            ),
            obs_otel_service_version=(
                env.str("OBS_OTEL_SERVICE_VERSION", default="0.1.0") or "0.1.0"
            ),
            obs_otel_environment=(
                env.str("OBS_OTEL_ENVIRONMENT", default=app_env) or app_env
            ),
            obs_otel_exporter_otlp_endpoint=obs_otel_exporter_otlp_endpoint,
            obs_otel_exporter_otlp_headers=obs_otel_exporter_otlp_headers,
            obs_otel_exporter_otlp_ca_cert_file=(
                obs_otel_exporter_otlp_ca_cert_file
            ),
            obs_otel_exporter_otlp_client_cert_file=(
                obs_otel_exporter_otlp_client_cert_file
            ),
            obs_otel_exporter_otlp_client_key_file=(
                obs_otel_exporter_otlp_client_key_file
            ),
            obs_otel_metrics_export_interval_ms=_require_positive_int(
                env.int("OBS_OTEL_METRICS_EXPORT_INTERVAL_MS", default=15000),
                "OBS_OTEL_METRICS_EXPORT_INTERVAL_MS",
            ),
            obs_otel_traces_sampler=(
                env.str("OBS_OTEL_TRACES_SAMPLER", default="traceidratio")
                or "traceidratio"
            ),
            obs_otel_traces_sampler_arg=env.float(
                "OBS_OTEL_TRACES_SAMPLER_ARG", default=0.1
            ),
            obs_otel_http_instrumentation_enabled=env.bool(
                "OBS_OTEL_HTTP_INSTRUMENTATION_ENABLED",
                default=True,
            ),
            obs_otel_sqlalchemy_instrumentation_enabled=env.bool(
                "OBS_OTEL_SQLALCHEMY_INSTRUMENTATION_ENABLED",
                default=False,
            ),
            obs_otel_redis_instrumentation_enabled=env.bool(
                "OBS_OTEL_REDIS_INSTRUMENTATION_ENABLED",
                default=False,
            ),
            obs_otel_capture_request_headers=env.bool(
                "OBS_OTEL_CAPTURE_REQUEST_HEADERS",
                default=False,
            ),
            obs_otel_capture_response_headers=env.bool(
                "OBS_OTEL_CAPTURE_RESPONSE_HEADERS",
                default=False,
            ),
            obs_otel_sanitize_fields_csv=(
                env.str(
                    "OBS_OTEL_SANITIZE_FIELDS_CSV",
                    default=(
                        ".*session.*,set-cookie,authorization,"
                        "proxy-authorization"
                    ),
                )
                or ".*session.*,set-cookie,authorization,proxy-authorization"
            ),
            obs_otel_semconv_stability_opt_in=(
                env.str(
                    "OBS_OTEL_SEMCONV_STABILITY_OPT_IN",
                    default="",
                )
                or None
            ),
        )


def is_prod_env(settings: Settings) -> bool:
    return settings.app_env.lower() in {"prod", "production"}
