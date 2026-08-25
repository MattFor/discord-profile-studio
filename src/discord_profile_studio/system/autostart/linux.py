import shutil
import sys
from pathlib import Path

from platformdirs import user_config_path

from discord_profile_studio.core.exceptions import AutostartError
from discord_profile_studio.system.autostart.base import APP_NAME, START_MINIMIZED, AutostartBackend

DESKTOP_FILE = "discord-profile-studio.desktop"


class LinuxAutostart(AutostartBackend):
    def __init__(self, autostart_dir: Path | None = None) -> None:
        self.autostart_dir: Path | None = autostart_dir

    def _dir(self) -> Path:
        if self.autostart_dir is not None:
            return self.autostart_dir
        return user_config_path() / "autostart"

    def _path(self) -> Path:
        return self._dir() / DESKTOP_FILE

    def _exec(self, *, minimized: bool) -> str:
        exe = shutil.which("discord-profile-studio-gui")
        if exe is None:
            exe = f"{sys.executable} -m discord_profile_studio"
        if minimized:
            exe = exe + " " + START_MINIMIZED
        return exe

    def enabled(self) -> bool:
        return self._path().exists()

    def enable(self, *, minimized: bool = True) -> None:
        try:
            self._dir().mkdir(parents=True, exist_ok=True)
            self._path().write_text(
                self.render_desktop_entry(minimized=minimized), encoding="utf-8"
            )
        except OSError as e:
            msg = f"Failed to enable autostart: {e}"
            raise AutostartError(msg) from e

    def disable(self) -> None:
        try:
            self._path().unlink(missing_ok=True)
        except OSError as e:
            msg = f"Failed to disable autostart: {e}"
            raise AutostartError(msg) from e

    def render_desktop_entry(self, *, minimized: bool) -> str:
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={APP_NAME}",
            f"Exec={self._exec(minimized=minimized)}",
            "Terminal=false",
            "X-GNOME-Autostart-enabled=true",
        ]
        return "\n".join(lines) + "\n"
