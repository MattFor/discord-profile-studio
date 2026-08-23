from dataclasses import dataclass


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


def load() -> Settings:
    raise NotImplementedError


def save(settings: Settings) -> None:
    raise NotImplementedError


def defaults() -> Settings:
    raise NotImplementedError
