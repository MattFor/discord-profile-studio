from discord_profile_studio.system.platform import has_display, is_linux
from discord_profile_studio.tray.backends._pystray import PystrayBackend


class LinuxTray(PystrayBackend):
    name = "linux"

    def available(self) -> bool:
        return is_linux() and has_display()
