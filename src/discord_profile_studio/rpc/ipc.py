from pathlib import Path


def candidate_sockets() -> list[Path]:
    raise NotImplementedError


def discover() -> Path:
    raise NotImplementedError


def is_discord_running() -> bool:
    raise NotImplementedError
