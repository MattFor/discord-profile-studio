import time
import tkinter as tk
from collections.abc import Iterator
from tkinter import TclError

import pytest
from pytest_mock import MockerFixture

from discord_profile_studio.gui.editor.fields import LabelledEntry
from discord_profile_studio.gui.editor.sections import widgets as section_module
from discord_profile_studio.gui.editor.sections.widgets import WidgetsSection
from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models import Favourite, FieldType, Widget, WidgetField
from discord_profile_studio.widgets.api import token_account
from tests.conftest import WIDGET_APP, FakeDiscord, MemoryStore

pytestmark = pytest.mark.gui


@pytest.fixture
def root() -> Iterator[tk.Tk]:
    try:
        instance = tk.Tk()
    except TclError:
        pytest.skip("no display server available")
    instance.withdraw()
    yield instance
    instance.destroy()


@pytest.fixture
def tokens(monkeypatch: pytest.MonkeyPatch) -> MemoryStore:
    tokens = MemoryStore()
    monkeypatch.setattr(section_module, "open_store", lambda: tokens)
    return tokens


@pytest.fixture
def state(favourite: Favourite) -> AppState:
    state = AppState()
    state.set_current(favourite)
    return state


@pytest.fixture
def section(root: tk.Tk, state: AppState, tokens: MemoryStore) -> WidgetsSection:
    assert tokens
    section = WidgetsSection(root, state)
    section.build()
    return section


def entries(widget: tk.Misc) -> list[LabelledEntry]:
    found: list[LabelledEntry] = []

    for child in widget.winfo_children():
        if isinstance(child, LabelledEntry):
            found.append(child)

        found += entries(child)

    return found


def settle(root: tk.Tk, section: WidgetsSection) -> None:
    deadline = time.monotonic() + 5

    while not section.add_button.instate(["!disabled"]):
        assert time.monotonic() < deadline, "the background call never finished"
        root.update()
        time.sleep(0.01)


def filled(state: AppState) -> None:
    fields = [
        WidgetField("rank", FieldType.TEXT, "Gold"),
        WidgetField("level", FieldType.NUMBER, "7"),
        WidgetField("cover", FieldType.IMAGE, "https://example.com/a.png"),
    ]
    state.current.widgets = [Widget(WIDGET_APP, "Stats", fields)]


def test_build_shows_the_current_favourites_widgets(section: WidgetsSection, state: AppState):
    assert section.to_model() == state.current.widgets
    assert [entry.variable.get() for entry in entries(section.scroll.inner)] == ["42"]


def test_editing_a_value_writes_it_to_the_state(section: WidgetsSection, state: AppState):
    seen: list[str] = []
    state.subscribe(lambda favourite: seen.append(favourite.widgets[0].fields[0].value))

    entries(section.scroll.inner)[0].variable.set("43")

    assert state.current.widgets[0].fields[0].value == "43"
    assert state.dirty is True
    assert seen == ["43"]


def test_remove_widget_drops_it_from_the_state(section: WidgetsSection, state: AppState):
    section.remove_widget(0)

    assert state.current.widgets == []
    assert entries(section.scroll.inner) == []


@pytest.mark.usefixtures("discord")
def test_add_fetches_the_fields_and_keeps_values_that_fit(
    root: tk.Tk,
    section: WidgetsSection,
    state: AppState,
):
    section.application.variable.set(WIDGET_APP)

    section.fetch()
    settle(root, section)

    fields = state.current.widgets[0].fields
    assert [(field.name, field.value) for field in fields] == [
        ("rank", ""),
        ("level", "42"),
        ("cover", ""),
    ]
    assert section.status.get() == "Added Stats, 2 value(s) to fill in"


@pytest.mark.usefixtures("discord")
def test_add_asks_for_a_missing_bot_token_and_stores_it(
    root: tk.Tk,
    section: WidgetsSection,
    tokens: MemoryStore,
    mocker: MockerFixture,
):
    tokens.tokens.clear()
    mocker.patch.object(section_module.simpledialog, "askstring", return_value=" fresh-token ")
    section.application.variable.set(WIDGET_APP)

    section.fetch()
    settle(root, section)

    assert tokens.tokens[token_account(WIDGET_APP)].access_token == "fresh-token"


@pytest.mark.usefixtures("discord")
def test_add_refuses_a_token_from_another_application(
    root: tk.Tk,
    section: WidgetsSection,
    tokens: MemoryStore,
    state: AppState,
):
    tokens.tokens[token_account("999")] = tokens.tokens[token_account(WIDGET_APP)]
    section.application.variable.set("999")

    section.fetch()
    settle(root, section)

    assert section.status.get() == f"that bot token belongs to application {WIDGET_APP}"
    assert len(state.current.widgets) == 1


def test_add_wants_a_numeric_application_id(section: WidgetsSection, discord: FakeDiscord):
    section.application.variable.set("stats")

    section.fetch()

    assert "numeric ID" in section.status.get()
    assert discord.calls == []


def test_push_reports_missing_values_and_sends_nothing(
    root: tk.Tk,
    section: WidgetsSection,
    discord: FakeDiscord,
):
    section.push()
    settle(root, section)

    assert section.status.get().startswith("not pushed, fix these first:")
    assert "Stats: rank: missing" in section.status.get()
    assert all(method != "PATCH" for method, *_ in discord.calls)


def test_push_sends_every_widget(
    root: tk.Tk,
    section: WidgetsSection,
    state: AppState,
    discord: FakeDiscord,
):
    filled(state)
    section.read()

    section.push()
    settle(root, section)

    assert section.status.get() == "Pushed 1 widget(s) to your profile"
    assert [method for method, *_ in discord.calls].count("PATCH") == 1
