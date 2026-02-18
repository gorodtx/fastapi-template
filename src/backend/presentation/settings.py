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
    refresh_lock_ttl_s: float
    refresh_lock_wait_timeout_s: float
    argon2_time_cost: int
    argon2_memory_cost_kib: int
    argon2_parallelism: int
    argon2_hash_len: int
    argon2_salt_len: int

    @staticmethod
    def from_env(env: Env) -> Settings:
        app_env: str = env.str("APP_ENV", default="dev") or "dev"
        redis_url: str | None = env.str("REDIS_URL", default="") or None
        default_registration_role_code = (
            env.str("DEFAULT_REGISTRATION_ROLE_CODE", default="user") or "user"
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
            jwt_access_ttl_s=_require_int(env, "JWT_ACCESS_TTL_S"),
            jwt_refresh_ttl_s=_require_int(env, "JWT_REFRESH_TTL_S"),
            refresh_lock_ttl_s=env.float("REFRESH_LOCK_TTL_S", default=10.0),
            refresh_lock_wait_timeout_s=env.float(
                "REFRESH_LOCK_WAIT_TIMEOUT_S",
                default=1.0,
            ),
            argon2_time_cost=env.int("ARGON2_TIME_COST", default=3),
            argon2_memory_cost_kib=env.int(
                "ARGON2_MEMORY_COST_KIB", default=65536
            ),
            argon2_parallelism=env.int("ARGON2_PARALLELISM", default=4),
            argon2_hash_len=env.int("ARGON2_HASH_LEN", default=32),
            argon2_salt_len=env.int("ARGON2_SALT_LEN", default=16),
        )


def is_prod_env(settings: Settings) -> bool:
    return settings.app_env.lower() in {"prod", "production"}
