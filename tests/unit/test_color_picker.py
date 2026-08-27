import tkinter as tk
from tkinter import TclError

import pytest

from discord_profile_studio.gui.components.color_picker import ColorPicker

MODULE = "discord_profile_studio.gui.components.color_picker"


@pytest.fixture
def root():
    try:
        instance = tk.Tk()
    except TclError:
        pytest.skip("no display server available")
    instance.withdraw()
    yield instance
    instance.destroy()


@pytest.fixture
def picker(root):
    widget = ColorPicker(root)
    widget.build()
    return widget


@pytest.mark.gui
def test_build_creates_children(picker):
    assert picker.winfo_children()


@pytest.mark.gui
def test_swatch_shows_initial_value(picker):
    assert picker.swatch.cget("bg") == picker.value.get()


@pytest.mark.gui
def test_label_follows_value(picker):
    picker.value.set("#123456")
    assert picker.label.cget("text") == "#123456"


@pytest.mark.gui
def test_choose_sets_value(picker, mocker):
    mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=((255, 0, 0), "#FF0000"))
    picker.choose()
    assert picker.value.get() == "#ff0000"


@pytest.mark.gui
def test_choose_normalises_case(picker, mocker):
    mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=((88, 101, 242), "#5865F2"))
    picker.choose()
    assert picker.value.get() == "#5865f2"


@pytest.mark.gui
def test_choose_adds_hash_prefix(picker, mocker):
    mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=((88, 101, 242), "5865F2"))
    picker.choose()
    assert picker.value.get() == "#5865f2"


@pytest.mark.gui
def test_choose_cancelled_keeps_value(picker, mocker):
    before = picker.value.get()
    mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=(None, None))
    picker.choose()
    assert picker.value.get() == before


@pytest.mark.gui
def test_choose_opens_dialog_with_current_colour(picker, mocker):
    fake = mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=(None, None))
    picker.value.set("#00ff00")
    picker.choose()
    assert fake.call_args.kwargs["color"] == "#00ff00"


@pytest.mark.gui
def test_choose_updates_swatch(picker, mocker):
    mocker.patch(f"{MODULE}.colorchooser.askcolor", return_value=((0, 255, 0), "#00FF00"))
    picker.choose()
    assert picker.swatch.cget("bg") == "#00ff00"


@pytest.mark.gui
def test_external_set_updates_swatch(picker):
    picker.value.set("#00ff00")
    assert picker.swatch.cget("bg") == "#00ff00"


@pytest.mark.gui
def test_invalid_value_keeps_previous_swatch(picker):
    picker.value.set("#00ff00")
    previous = picker.swatch.cget("bg")
    picker.value.set("not-a-colour")
    assert picker.swatch.cget("bg") == previous
