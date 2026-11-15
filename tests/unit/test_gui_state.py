from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models import Favourite


def test_previewed_is_the_hovered_favourite_while_one_is_hovered():
    state = AppState()
    hovered = Favourite(name="Gaming")

    state.set_hovered(hovered)
    assert state.previewed is hovered

    state.set_hovered(None)
    assert state.previewed is state.current


def test_listeners_get_the_previewed_favourite_until_they_unsubscribe():
    state = AppState()
    seen: list[str] = []
    unsubscribe = state.subscribe(lambda favourite: seen.append(favourite.name))

    state.set_current(Favourite(name="Coding"))
    unsubscribe()
    state.set_current(Favourite(name="Gaming"))

    assert seen == ["Coding"]


def test_a_listener_may_unsubscribe_while_being_notified():
    state = AppState()
    seen: list[str] = []
    unsubscribe = state.subscribe(lambda _: unsubscribe())
    state.subscribe(lambda favourite: seen.append(favourite.name))

    state.set_current(Favourite(name="Coding"))
    state.notify()

    assert seen == ["Coding", "Coding"]


def test_set_current_clears_dirty():
    state = AppState()
    state.dirty = True

    state.set_current(Favourite(name="Coding"))

    assert state.dirty is False
