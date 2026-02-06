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

        return Settings(
            app_env=app_env,
            database_url=_require_str(env, "DATABASE_URL"),
            redis_url=redis_url,
            jwt_issuer=_require_str(env, "JWT_ISSUER"),
            jwt_audience=_require_str(env, "JWT_AUDIENCE"),
            jwt_alg=_require_str(env, "JWT_ALG"),
            jwt_secret=_require_str(env, "JWT_SECRET"),
            jwt_access_ttl_s=_require_int(env, "JWT_ACCESS_TTL_S"),
            jwt_refresh_ttl_s=_require_int(env, "JWT_REFRESH_TTL_S"),
        )


def is_prod_env(settings: Settings) -> bool:
    return settings.app_env.lower() in {"prod", "production"}
