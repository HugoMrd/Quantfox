import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def connection_string(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.name} user={self.user} password={self.password}"


@dataclass
class CeleryConfig:
    broker_url: str
    result_backend: str


@dataclass
class ServerConfig:
    host: str
    port: int


@dataclass
class Config:
    database: DatabaseConfig
    celery: CeleryConfig
    server: ServerConfig


def load_config(config_path: Optional[str] = None) -> Config:
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config.toml")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return Config(
        database=DatabaseConfig(
            host=data["database"]["host"],
            port=data["database"]["port"],
            name=data["database"]["name"],
            user=data["database"]["user"],
            password=data["database"]["password"],
        ),
        celery=CeleryConfig(
            broker_url=data["celery"]["broker_url"],
            result_backend=data["celery"]["result_backend"],
        ),
        server=ServerConfig(
            host=data["server"]["host"],
            port=data["server"]["port"],
        ),
    )


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config
