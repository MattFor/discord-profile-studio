from pathlib import Path

APP_NAME = "discord-profile-studio"


def config_dir() -> Path:
    raise NotImplementedError


def data_dir() -> Path:
    raise NotImplementedError


def cache_dir() -> Path:
    raise NotImplementedError


def runtime_dir() -> Path:
    raise NotImplementedError


def settings_file() -> Path:
    raise NotImplementedError


def favourites_file() -> Path:
    raise NotImplementedError


def token_file() -> Path:
    raise NotImplementedError


def lock_file() -> Path:
    raise NotImplementedError


def log_file() -> Path:
    raise NotImplementedError


def ensure_private(path: Path) -> Path:
    raise NotImplementedError
