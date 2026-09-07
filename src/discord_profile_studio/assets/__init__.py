from pathlib import Path

ROOT = Path(__file__).parent
ICONS = ROOT / "icons"
FONTS = ROOT / "fonts"

TRAY_CONNECTED = ICONS / "tray_connected.png"
TRAY_IDLE = ICONS / "tray_idle.png"

__all__ = ["FONTS", "ICONS", "ROOT", "TRAY_CONNECTED", "TRAY_IDLE", "tray_icon"]


def tray_icon(*, connected: bool) -> Path:
    return TRAY_CONNECTED if connected else TRAY_IDLE
