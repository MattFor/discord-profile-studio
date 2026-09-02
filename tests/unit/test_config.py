import json
import stat
import sys

import pytest

from discord_profile_studio.core.config import Settings, defaults, load, save, to_dict
from discord_profile_studio.core.exceptions import ConfigError
from discord_profile_studio.core.paths import (
    ensure_private,
    settings_file,
    token_file,
    write_private,
)

on_posix = pytest.mark.skipif(sys.platform == "win32", reason="requires POSIX file modes")


@pytest.fixture
def settings_path(tmp_path):
    return tmp_path / "config" / "settings.json"


def test_load_falls_back_to_defaults(settings_path):
    assert load(settings_path) == defaults()


def test_save_and_load_roundtrip(settings_path):
    settings = Settings(account="main", token_backend="encrypted-file", close_to_tray=False)

    save(settings, settings_path)

    assert load(settings_path) == settings


def test_save_writes_readable_json(settings_path):
    save(Settings(), settings_path)

    assert json.loads(settings_path.read_text(encoding="utf-8")) == to_dict(Settings())


def test_load_ignores_unknown_keys(settings_path):
    write_private(settings_path, json.dumps({"account": "main", "colour": "blurple"}))

    assert load(settings_path).account == "main"


def test_load_ignores_values_of_the_wrong_type(settings_path):
    write_private(settings_path, json.dumps({"close_to_tray": "yes", "account": "main"}))
    settings = load(settings_path)

    assert settings.close_to_tray is True
    assert settings.account == "main"


@pytest.mark.parametrize("contents", ["not json", "[]", '"settings"'])
def test_load_rejects_malformed_settings(settings_path, contents):
    write_private(settings_path, contents)

    with pytest.raises(ConfigError):
        load(settings_path)


@on_posix
def test_save_keeps_the_settings_private(settings_path):
    save(Settings(), settings_path)

    assert stat.S_IMODE(settings_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(settings_path.parent.stat().st_mode) == 0o700


def test_write_private_replaces_the_previous_contents(tmp_path):
    path = tmp_path / "notes.txt"

    write_private(path, "first")
    write_private(path, "second")

    assert path.read_text(encoding="utf-8") == "second"
    assert not (tmp_path / "notes.txt.tmp").exists()


def test_write_private_accepts_bytes(tmp_path):
    path = write_private(tmp_path / "blob.bin", b"\x00\x01\x02")

    assert path.read_bytes() == b"\x00\x01\x02"


def test_ensure_private_creates_the_parent(tmp_path):
    ensure_private(tmp_path / "nested" / "deeper" / "tokens.enc")

    assert (tmp_path / "nested" / "deeper").is_dir()


def test_the_token_file_sits_under_the_data_directory():
    assert token_file().name == "tokens.enc"
    assert token_file().parent.name == "discord-profile-studio"


def test_the_settings_file_sits_under_the_config_directory():
    assert settings_file().name == "settings.json"
    assert settings_file().parent.name == "discord-profile-studio"
