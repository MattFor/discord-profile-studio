import sys
from typing import LiteralString

from discord_profile_studio.core.exceptions import AutostartError
from discord_profile_studio.system.autostart.base import AutostartBackend


def backend() -> AutostartBackend:
    if sys.platform == "win32":
        from discord_profile_studio.system.autostart.windows import WindowsAutostart  # noqa: I001, PLC0415

        return WindowsAutostart()

    if sys.platform == "linux":
        from discord_profile_studio.system.autostart.linux import LinuxAutostart  # noqa: I001, PLC0415

        return LinuxAutostart()

    msg: LiteralString = f"Autostart is not supported on platform {sys.platform}"
    raise AutostartError(msg)
