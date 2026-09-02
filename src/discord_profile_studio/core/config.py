import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, cast

from discord_profile_studio.core.exceptions import ConfigError
from discord_profile_studio.core.paths import settings_file, write_private


@dataclass(slots=True)
class Settings:
    account: str = ""
    theme: str = "dark"
    autoconnect: bool = False
    autostart: bool = False
    start_minimized: bool = False
    close_to_tray: bool = True
    token_backend: str = "keyring"
    hover_preview_delay_ms: int = 120


def defaults() -> Settings:
    return Settings()


def from_dict(data: dict[str, Any]) -> Settings:
    settings = defaults()

    for entry in fields(Settings):
        if entry.name not in data:
            continue

        value = data[entry.name]

        if type(value) is type(getattr(settings, entry.name)):
            setattr(settings, entry.name, value)

    return settings


def to_dict(settings: Settings) -> dict[str, Any]:
    return asdict(settings)


def load(path: Path | None = None) -> Settings:
    target = path or settings_file()

    if not target.exists():
        return defaults()

    try:
        loaded: Any = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        msg = f"Could not read the settings at {target}: {e}"
        raise ConfigError(msg) from e

    if not isinstance(loaded, dict):
        msg = f"The settings at {target} are malformed"
        raise ConfigError(msg)

    return from_dict(cast("dict[str, Any]", loaded))


def save(settings: Settings, path: Path | None = None) -> None:
    target = path or settings_file()

    try:
        write_private(target, json.dumps(to_dict(settings), indent=2) + "\n")
    except OSError as e:
        msg = f"Could not write the settings at {target}: {e}"
        raise ConfigError(msg) from e
