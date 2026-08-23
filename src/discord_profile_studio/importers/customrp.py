from pathlib import Path

from discord_profile_studio.models.favourite import Favourite


def default_config_paths() -> list[Path]:
    raise NotImplementedError


def load_preset(path: Path) -> Favourite:
    raise NotImplementedError


def load_settings(path: Path) -> Favourite:
    raise NotImplementedError


def load_all(directory: Path) -> list[Favourite]:
    raise NotImplementedError
