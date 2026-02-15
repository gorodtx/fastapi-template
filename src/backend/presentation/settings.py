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
        )


def is_prod_env(settings: Settings) -> bool:
    return settings.app_env.lower() in {"prod", "production"}
