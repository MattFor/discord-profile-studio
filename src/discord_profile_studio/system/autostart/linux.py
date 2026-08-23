from pathlib import Path

from discord_profile_studio.system.autostart.base import AutostartBackend

DESKTOP_FILE = "discord-profile-studio.desktop"


class LinuxAutostart(AutostartBackend):
    def __init__(self, autostart_dir: Path | None = None) -> None:
        self.autostart_dir = autostart_dir

    def enabled(self) -> bool:
        raise NotImplementedError

    def enable(self, *, minimized: bool = True) -> None:
        raise NotImplementedError

    def disable(self) -> None:
        raise NotImplementedError

    def render_desktop_entry(self, *, minimized: bool) -> str:
        raise NotImplementedError
