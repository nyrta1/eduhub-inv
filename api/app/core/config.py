from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pydantic import Field, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded exclusively from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_name: str = Field(default="student-platform-api", validation_alias="APP_NAME")
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")

    app_secret_key: str = Field(
        ...,
        min_length=32,
        validation_alias="APP_SECRET_KEY",
        description="Cryptographic secret for signing; must be set via environment.",
    )

    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")  # nosec B104
    api_port: int = Field(default=8000, ge=1, le=65535, validation_alias="API_PORT")

    api_allowed_hosts: str = Field(
        default="localhost,127.0.0.1",
        validation_alias="API_ALLOWED_HOSTS",
        description="Comma-separated hostnames for TrustedHostMiddleware.",
    )

    cors_allowed_origins: str = Field(
        default="",
        validation_alias="CORS_ALLOWED_ORIGINS",
        description="Comma-separated origins; empty disables CORS.",
    )

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")

    db_pool_size: int = Field(default=10, ge=1, le=100, validation_alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(
        default=20,
        ge=0,
        le=200,
        validation_alias="DB_MAX_OVERFLOW",
    )
    db_pool_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        validation_alias="DB_POOL_TIMEOUT_SECONDS",
    )
    db_pool_recycle_seconds: int = Field(
        default=1800,
        ge=60,
        le=86400,
        validation_alias="DB_POOL_RECYCLE_SECONDS",
    )

    redis_url: str = Field(..., validation_alias="REDIS_URL")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_json: bool = Field(default=True, validation_alias="LOG_JSON")
    structlog_caller_info: bool = Field(
        default=False,
        validation_alias="STRUCTLOG_CALLER_INFO",
    )

    log_ship_logstash: bool = Field(default=False, validation_alias="LOG_SHIP_LOGSTASH")
    logstash_http_endpoint: str = Field(
        default="http://logstash:5044",
        validation_alias="LOGSTASH_HTTP_ENDPOINT",
    )

    metrics_enabled: bool = Field(default=True, validation_alias="METRICS_ENABLED")
    metrics_path: str = Field(default="/metrics", validation_alias="METRICS_PATH")

    request_max_body_bytes: int = Field(
        default=1_048_576,
        ge=1024,
        le=100_000_000,
        validation_alias="REQUEST_MAX_BODY_BYTES",
    )

    jwt_issuer: str = Field(default="student-platform-api", validation_alias="JWT_ISSUER")
    jwt_audience_access: str = Field(
        default="student-platform-access",
        validation_alias="JWT_AUDIENCE_ACCESS",
    )
    jwt_audience_refresh: str = Field(
        default="student-platform-refresh",
        validation_alias="JWT_AUDIENCE_REFRESH",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_ttl_seconds: int = Field(
        default=900,
        ge=60,
        le=3600,
        validation_alias="JWT_ACCESS_TTL_SECONDS",
    )
    jwt_refresh_ttl_seconds: int = Field(
        default=604_800,
        ge=600,
        le=2_592_000,
        validation_alias="JWT_REFRESH_TTL_SECONDS",
    )
    jwt_access_secret: str | None = Field(default=None, validation_alias="JWT_ACCESS_SECRET")
    jwt_refresh_secret: str | None = Field(default=None, validation_alias="JWT_REFRESH_SECRET")

    token_pepper: str | None = Field(
        default=None,
        validation_alias="TOKEN_PEPPER",
        description="Server-side pepper for refresh token fingerprinting.",
    )

    password_history_limit: int = Field(
        default=5,
        ge=1,
        le=24,
        validation_alias="PASSWORD_HISTORY_LIMIT",
    )

    auth_max_failed_logins: int = Field(
        default=5,
        ge=3,
        le=20,
        validation_alias="AUTH_MAX_FAILED_LOGINS",
    )
    auth_lockout_seconds: int = Field(
        default=900,
        ge=60,
        le=86_400,
        validation_alias="AUTH_LOCKOUT_SECONDS",
    )

    auth_login_max_per_ip_per_minute: int = Field(
        default=30,
        ge=5,
        le=1000,
        validation_alias="AUTH_LOGIN_MAX_PER_IP_PER_MINUTE",
    )
    auth_login_max_per_email_per_minute: int = Field(
        default=15,
        ge=3,
        le=500,
        validation_alias="AUTH_LOGIN_MAX_PER_EMAIL_PER_MINUTE",
    )
    auth_register_max_per_ip_per_hour: int = Field(
        default=10,
        ge=1,
        le=200,
        validation_alias="AUTH_REGISTER_MAX_PER_IP_PER_HOUR",
    )
    auth_refresh_max_per_session_per_minute: int = Field(
        default=30,
        ge=5,
        le=500,
        validation_alias="AUTH_REFRESH_MAX_PER_SESSION_PER_MINUTE",
    )

    security_expose_openapi: bool = Field(
        default=False,
        validation_alias="SECURITY_EXPOSE_OPENAPI",
        description="When true, expose OpenAPI/Scalar docs (never enable in production without intent).",
    )

    security_headers_enabled: bool = Field(default=True, validation_alias="SECURITY_HEADERS_ENABLED")
    security_csp: str = Field(
        default="default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        validation_alias="SECURITY_CSP",
    )
    security_hsts_max_age: int = Field(
        default=31536000,
        ge=0,
        le=63072000,
        validation_alias="SECURITY_HSTS_MAX_AGE",
    )
    security_hsts_include_subdomains: bool = Field(
        default=True,
        validation_alias="SECURITY_HSTS_INCLUDE_SUBDOMAINS",
    )
    security_permissions_policy: str = Field(
        default="accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
        validation_alias="SECURITY_PERMISSIONS_POLICY",
    )
    security_referrer_policy: str = Field(
        default="strict-origin-when-cross-origin",
        validation_alias="SECURITY_REFERRER_POLICY",
    )
    security_cache_control_sensitive: str = Field(
        default="no-store, no-cache, must-revalidate, private",
        validation_alias="SECURITY_CACHE_CONTROL_SENSITIVE",
    )

    api_academic_application_submit_per_ip_per_hour: int = Field(
        default=60,
        ge=5,
        le=10_000,
        validation_alias="API_ACADEMIC_APPLICATION_SUBMIT_PER_IP_PER_HOUR",
    )
    api_academic_grade_write_per_ip_per_minute: int = Field(
        default=120,
        ge=10,
        le=10_000,
        validation_alias="API_ACADEMIC_GRADE_WRITE_PER_IP_PER_MINUTE",
    )
    api_academic_grade_write_per_token_per_minute: int = Field(
        default=60,
        ge=5,
        le=5000,
        validation_alias="API_ACADEMIC_GRADE_WRITE_PER_TOKEN_PER_MINUTE",
    )
    api_admin_role_change_per_ip_per_hour: int = Field(
        default=40,
        ge=5,
        le=2000,
        validation_alias="API_ADMIN_ROLE_CHANGE_PER_IP_PER_HOUR",
    )
    api_application_review_per_ip_per_minute: int = Field(
        default=200,
        ge=20,
        le=10_000,
        validation_alias="API_APPLICATION_REVIEW_PER_IP_PER_MINUTE",
    )

    security_denied_burst_threshold_per_ip: int = Field(
        default=25,
        ge=5,
        le=1000,
        validation_alias="SECURITY_DENIED_BURST_THRESHOLD_PER_IP",
    )
    security_denied_burst_window_seconds: int = Field(
        default=120,
        ge=30,
        le=3600,
        validation_alias="SECURITY_DENIED_BURST_WINDOW_SECONDS",
    )

    secure_http_default_timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=120.0,
        validation_alias="SECURE_HTTP_DEFAULT_TIMEOUT_SECONDS",
    )

    @field_validator("database_url")
    @classmethod
    def validate_async_database_url(cls, value: str) -> str:
        lowered = value.strip()
        if not lowered.startswith(
            ("postgresql+asyncpg://", "postgresql+psycopg://"),
        ):
            raise ValueError(
                "DATABASE_URL must use an async driver prefix "
                "(postgresql+asyncpg:// or postgresql+psycopg://).",
            )
        return lowered

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        RedisDsn(value)
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        upper = value.upper()
        if upper not in logging.getLevelNamesMapping():
            allowed = ", ".join(sorted(logging.getLevelNamesMapping()))
            raise ValueError(f"LOG_LEVEL must be one of: {allowed}")
        return upper

    @model_validator(mode="after")
    def enforce_production_hardening(self) -> Settings:
        env = self.app_env.lower()
        if env == "production":
            if self.app_debug:
                raise ValueError("APP_DEBUG must be false when APP_ENV is production.")
            if self.database_echo:
                raise ValueError("DATABASE_ECHO must be false when APP_ENV is production.")
        return self

    @model_validator(mode="after")
    def derive_auth_material(self) -> Settings:
        access_secret = self.jwt_access_secret or self.app_secret_key
        refresh_secret = self.jwt_refresh_secret or self.app_secret_key
        pepper = self.token_pepper or self.app_secret_key
        if len(access_secret) < 32 or len(refresh_secret) < 32:
            raise ValueError("JWT secrets must be at least 32 characters.")
        object.__setattr__(self, "_jwt_access_secret_resolved", access_secret)
        object.__setattr__(self, "_jwt_refresh_secret_resolved", refresh_secret)
        object.__setattr__(self, "_token_pepper_resolved", pepper)
        return self

    def resolved_jwt_access_secret(self) -> str:
        return getattr(self, "_jwt_access_secret_resolved")

    def resolved_jwt_refresh_secret(self) -> str:
        return getattr(self, "_jwt_refresh_secret_resolved")

    def resolved_token_pepper(self) -> str:
        return getattr(self, "_token_pepper_resolved")

    def parsed_allowed_hosts(self) -> list[str]:
        return [host.strip() for host in self.api_allowed_hosts.split(",") if host.strip()]

    def parsed_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    def expose_api_documentation(self) -> bool:
        """Interactive OpenAPI/Scalar docs: off in production unless explicitly enabled."""
        return self.app_env.lower() != "production" or self.security_expose_openapi

    def safe_settings_summary(self) -> dict[str, Any]:
        """Structured subset safe for logs and diagnostics (no secrets)."""
        return {
            "app_env": self.app_env,
            "app_name": self.app_name,
            "app_debug": self.app_debug,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "database_echo": self.database_echo,
            "db_pool_size": self.db_pool_size,
            "db_max_overflow": self.db_max_overflow,
            "log_level": self.log_level,
            "log_json": self.log_json,
            "log_ship_logstash": self.log_ship_logstash,
            "metrics_enabled": self.metrics_enabled,
            "metrics_path": self.metrics_path,
            "request_max_body_bytes": self.request_max_body_bytes,
            "jwt_issuer": self.jwt_issuer,
            "jwt_algorithm": self.jwt_algorithm,
            "jwt_access_ttl_seconds": self.jwt_access_ttl_seconds,
            "jwt_refresh_ttl_seconds": self.jwt_refresh_ttl_seconds,
            "auth_max_failed_logins": self.auth_max_failed_logins,
            "auth_lockout_seconds": self.auth_lockout_seconds,
            "security_headers_enabled": self.security_headers_enabled,
            "security_expose_openapi": self.security_expose_openapi,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
