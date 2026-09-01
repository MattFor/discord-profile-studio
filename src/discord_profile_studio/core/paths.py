import sys
from pathlib import Path

from platformdirs import (
    user_cache_path,
    user_config_path,
    user_data_path,
    user_log_path,
    user_runtime_path,
)

APP_NAME = "discord-profile-studio"
DIR_MODE = 0o700
FILE_MODE = 0o600


def config_dir() -> Path:
    return user_config_path(APP_NAME, appauthor=False)


def data_dir() -> Path:
    return user_data_path(APP_NAME, appauthor=False)


def cache_dir() -> Path:
    return user_cache_path(APP_NAME, appauthor=False)


def runtime_dir() -> Path:
    return user_runtime_path(APP_NAME, appauthor=False)


def settings_file() -> Path:
    return config_dir() / "settings.json"


def favourites_file() -> Path:
    return data_dir() / "favourites.json"


def token_file() -> Path:
    return data_dir() / "tokens.enc"


def lock_file() -> Path:
    return runtime_dir() / "dps.lock"


def log_file() -> Path:
    return user_log_path(APP_NAME, appauthor=False) / "dps.log"


def restrict(path: Path, mode: int) -> None:
    if sys.platform == "win32":
        return

    path.chmod(mode)


def ensure_private(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    restrict(path.parent, DIR_MODE)  # Owner only

    if path.exists():
        restrict(path, FILE_MODE)

    return path


def write_private(path: Path, data: str | bytes) -> Path:
    ensure_private(path)  # Make sure it has correct perms + exists

    # Temporary file first so target file isn't overwrittten
    temporary = path.with_name(path.name + ".tmp")

    # Temporary file with restricted perms
    temporary.touch(mode=FILE_MODE)
    restrict(temporary, FILE_MODE)

    # Text / Bin
    if isinstance(data, str):
        temporary.write_text(data, encoding="utf-8")
    else:
        temporary.write_bytes(data)

    # Replace og file with the temporary one
    temporary.replace(path)
    restrict(path, FILE_MODE)

    return path
