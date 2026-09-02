from discord_profile_studio.system.platform import is_windows
from discord_profile_studio.tray.backends._pystray import PystrayBackend


class WindowsTray(PystrayBackend):
    name = "windows"

    def available(self) -> bool:
        return is_windows()
