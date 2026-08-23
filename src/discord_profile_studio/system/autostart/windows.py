from discord_profile_studio.system.autostart.base import AutostartBackend

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class WindowsAutostart(AutostartBackend):
    def enabled(self) -> bool:
        raise NotImplementedError

    def enable(self, *, minimized: bool = True) -> None:
        raise NotImplementedError

    def disable(self) -> None:
        raise NotImplementedError
