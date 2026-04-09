"""
config.py – Central settings loaded from .env via Pydantic Settings.
All secrets/paths are read from environment variables; never hardcoded.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(3306, env="DB_PORT")
    db_user: str = Field("hms_user", env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    db_name: str = Field("hms_db", env="DB_NAME")
    db_pool_size: int = Field(10, env="DB_POOL_SIZE")

    # ── JWT ───────────────────────────────────────
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # ── Faster-Whisper ────────────────────────────
    whisper_model_size: str = Field("distil-large-v3", env="WHISPER_MODEL_SIZE")
    whisper_device: str = Field("cpu", env="WHISPER_DEVICE")
    whisper_compute_type: str = Field("int8", env="WHISPER_COMPUTE_TYPE")

    # ── App ───────────────────────────────────────
    app_env: str = Field("development", env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    cors_origins: str = Field("http://localhost:3000", env="CORS_ORIGINS")

    # ── Audio ─────────────────────────────────────
    audio_upload_dir: str = Field("./uploads/audio", env="AUDIO_UPLOAD_DIR")
    ffmpeg_path: str = Field("ffmpeg", env="FFMPEG_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — reads .env once at startup."""
    return Settings()
