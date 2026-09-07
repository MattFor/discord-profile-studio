from discord_profile_studio.core.exceptions import TrayUnavailableError
from discord_profile_studio.system.platform import Platform, current, has_display
from discord_profile_studio.tray.backends.base import TrayBackend


def _windows() -> TrayBackend:
    try:
        from discord_profile_studio.tray.backends.windows import WindowsTray  # noqa: PLC0415
    except ImportError as e:
        msg = "The pystray Windows backend could not be imported"
        raise TrayUnavailableError(msg) from e

    return WindowsTray()


def _linux() -> TrayBackend:
    if not has_display():
        msg = "No graphical session is available for the tray"
        raise TrayUnavailableError(msg)
    try:
        from discord_profile_studio.tray.backends.linux import LinuxTray  # noqa: PLC0415
    except Exception as e:
        msg = "The pystray Linux backend could not be loaded"
        raise TrayUnavailableError(msg) from e
    return LinuxTray()


def select() -> TrayBackend:
    kind = current()
    if kind == Platform.WINDOWS:
        backend = _windows()
    elif kind == Platform.LINUX:
        backend = _linux()
    else:
        msg = f"Tray is not supported on {kind.value}"
        raise TrayUnavailableError(msg)

    if not backend.available():
        msg = f"The {backend.name} tray backend reported itself as unavailable"
        raise TrayUnavailableError(msg)

    return backend
