import shutil
import sys
import winreg
from pathlib import Path

from discord_profile_studio.core.exceptions import AutostartError
from discord_profile_studio.system.autostart.base import APP_NAME, START_MINIMIZED, AutostartBackend

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class WindowsAutostart(AutostartBackend):
    def __init__(self, value_name: str = APP_NAME) -> None:
        self.value_name: str = value_name

    def _target(self) -> str:
        exe = shutil.which("discord-profile-studio-gui")
        if exe:
            return f'"{exe}"'

        py = Path(sys.executable)
        if py.name.lower() == "python.exe":
            py = py.with_name(name="pythonw.exe")
        return f'"{py}" -m discord_profile_studio'

    def _command(self, *, minimized: bool) -> str:
        cmd = self._target()
        if minimized:
            cmd = cmd + " " + START_MINIMIZED
        return cmd

    def enabled(self) -> bool:
        try:
            with winreg.OpenKey(
                key=winreg.HKEY_CURRENT_USER, sub_key=RUN_KEY, reserved=0, access=winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, self.value_name)
        except FileNotFoundError:
            return False
        except OSError as e:
            msg = "Failed to read autostart state"
            raise AutostartError(msg) from e
        else:
            return self._target() in value

    def enable(self, *, minimized: bool = True) -> None:
        try:
            with winreg.CreateKeyEx(
                key=winreg.HKEY_CURRENT_USER,
                sub_key=RUN_KEY,
                reserved=0,
                access=winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(
                    key, self.value_name, 0, winreg.REG_SZ, self._command(minimized=minimized)
                )
        except OSError as e:
            msg = f"Failed to enable autostart: {e}"
            raise AutostartError(msg) from e

    def disable(self) -> None:
        try:
            with winreg.OpenKey(
                key=winreg.HKEY_CURRENT_USER,
                sub_key=RUN_KEY,
                reserved=0,
                access=winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, self.value_name)
        except FileNotFoundError:
            return
        except OSError as e:
            msg = f"Failed to disable autostart: {e}"
            raise AutostartError(msg) from e
