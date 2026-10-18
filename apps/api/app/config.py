import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import URL

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: URL
    encryption_key: str
    secure_cookies: bool = False
    session_days: int = 14
    max_upload_bytes: int = 5 * 1024 * 1024


def load_dotenv(path: Path) -> None:
    """Load KEY="value" lines without overriding variables already in the environment."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_settings() -> Settings:
    load_dotenv(REPO_ROOT / ".env")
    config_path = Path(os.environ.get("CONFIG_PATH", REPO_ROOT / "config.yml"))
    config: dict[str, Any] = {}
    if config_path.is_file():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            config = loaded

    database = config.get("database", {})
    database_url = URL.create(
        "postgresql+psycopg",
        username=_required_env("DATABASE_USERNAME"),
        password=_required_env("DATABASE_PASSWORD"),
        host=str(database.get("host", "localhost")),
        port=int(database.get("port", 5433)),
        database=os.environ.get("DATABASE_NAME", str(database.get("name", "finance_os_dev"))),
    )
    environment = str(config.get("app", {}).get("environment", "development"))
    return Settings(
        database_url=database_url,
        encryption_key=_required_env("ENCRYPTION_KEY"),
        secure_cookies=environment != "development",
    )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set; copy .env.example to .env and fill it in")
    return value
