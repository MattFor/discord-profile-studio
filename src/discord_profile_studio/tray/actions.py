from discord_profile_studio.gui.controller import StudioController
from discord_profile_studio.tray.menu import TrayMenu


def build_menu(controller: StudioController) -> TrayMenu:
    raise NotImplementedError


def show_window(controller: StudioController) -> None:
    raise NotImplementedError


def toggle_presence(controller: StudioController) -> None:
    raise NotImplementedError


def quit_app(controller: StudioController) -> None:
    raise NotImplementedError
