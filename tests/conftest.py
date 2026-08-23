from pathlib import Path

import pytest

from discord_profile_studio.models.favourite import Favourite


@pytest.fixture
def favourite() -> Favourite:
    raise NotImplementedError


@pytest.fixture
def store(tmp_path: Path) -> Path:
    raise NotImplementedError
