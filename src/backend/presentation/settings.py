from __future__ import annotations

from dataclasses import dataclass

from environs import Env


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


def _require_positive_float(value: float, name: str) -> float:
    if value <= 0:
        raise RuntimeError(
            f"Environment variable must be positive number: {name}"
        )
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    database_url: str
    redis_url: str | None
    default_registration_role_code: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout_s: int
    db_pool_recycle_s: int
    db_connect_timeout_s: int

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
        redis_url: str | None = env.str("REDIS_URL", default="") or None
        default_registration_role_code = (
            env.str("DEFAULT_REGISTRATION_ROLE_CODE", default="user") or "user"
        )
        obs_otel_enabled = env.bool("OBS_OTEL_ENABLED", default=False)
        obs_otel_exporter_otlp_endpoint = (
            env.str("OBS_OTEL_EXPORTER_OTLP_ENDPOINT", default="") or None
        )

        return Settings(
            app_env=app_env,
            database_url=_require_str(env, "DATABASE_URL"),
            redis_url=redis_url,
            default_registration_role_code=default_registration_role_code,
            db_pool_size=env.int("DB_POOL_SIZE", default=10),
            db_max_overflow=env.int("DB_MAX_OVERFLOW", default=20),
            db_pool_timeout_s=env.int("DB_POOL_TIMEOUT_S", default=30),
            db_pool_recycle_s=env.int("DB_POOL_RECYCLE_S", default=1800),
            db_connect_timeout_s=env.int("DB_CONNECT_TIMEOUT_S", default=10),
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
