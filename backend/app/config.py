"""Configuration management."""
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


def _expand_env_vars(value: Any) -> Any:
    """Expand environment variables in config values."""
    if isinstance(value, str):
        # Handle ${VAR:-default} or ${VAR} format
        pattern = r'\$\{([^}]+)\}'
        match = re.search(pattern, value)
        if match:
            env_expr = match.group(1)
            if ':-' in env_expr:
                var_name, default = env_expr.split(':-', 1)
                env_value = os.environ.get(var_name, default)
            elif ':' in env_expr:
                var_name, default = env_expr.split(':', 1)
                env_value = os.environ.get(var_name, default)
            else:
                env_value = os.environ.get(env_expr, '')
            return re.sub(pattern, env_value, value)
    return value


def _process_config(data: dict) -> dict:
    """Recursively process config data to expand environment variables."""
    if data is None:
        return None
    processed = {}
    for key, value in data.items():
        if isinstance(value, dict):
            processed[key] = _process_config(value)
        elif isinstance(value, list):
            processed[key] = [_expand_env_vars(item) if isinstance(item, str) else item for item in value]
        else:
            processed[key] = _expand_env_vars(value)
    return processed


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    secret_key: str = "change-this-in-production"


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = "postgres"
    name: str = "chat_data"
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class StorageConfig(BaseModel):
    endpoint: str = "localhost:9000"
    access_key: str = ""
    secret_key: str = ""
    bucket: str = "chat-data"
    secure: bool = False


class AIConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096


class CeleryConfig(BaseModel):
    result_expires: int = 3600
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list = ["json"]
    timezone: str = "UTC"


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    storage: StorageConfig = StorageConfig()
    ai: AIConfig = AIConfig()
    celery: CeleryConfig = CeleryConfig()

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """Load settings from YAML file."""
        if not Path(config_path).exists():
            return cls()

        with open(config_path) as f:
            config_data = yaml.safe_load(f) or {}

        # Process environment variables
        config_data = _process_config(config_data)

        # Recursively build nested configs
        def build_nested(obj_class: type, data: dict) -> Any:
            if data is None:
                return obj_class()
            return obj_class(**data)

        return cls(
            app=build_nested(AppConfig, config_data.get("app")),
            database=build_nested(DatabaseConfig, config_data.get("database")),
            redis=build_nested(RedisConfig, config_data.get("redis")),
            storage=build_nested(StorageConfig, config_data.get("storage")),
            ai=build_nested(AIConfig, config_data.get("ai")),
            celery=build_nested(CeleryConfig, config_data.get("celery")),
        )


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml(
            Path(__file__).parent.parent / "config.yaml"
        )
    return _settings
