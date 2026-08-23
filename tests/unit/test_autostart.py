import pytest


@pytest.mark.windows
@pytest.mark.skip
def test_windows_run_key() -> None:
    raise NotImplementedError


@pytest.mark.linux
@pytest.mark.skip
def test_linux_desktop_entry() -> None:
    raise NotImplementedError
