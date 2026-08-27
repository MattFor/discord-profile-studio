import pytest

from discord_profile_studio.tray.menu import TrayMenu, TrayMenuItem


def item(label, submenu=None):
    return TrayMenuItem(label=label, submenu=submenu)


def sep():
    return TrayMenuItem(separator=True)


def labels(menu):
    return [entry.label or "|" for entry in menu.items]


def test_add_appends_to_end():
    menu = TrayMenu()
    menu.add(item("Show"))
    assert labels(menu) == ["Show"]


def test_add_keeps_order():
    menu = TrayMenu()
    menu.add(item("Show"))
    menu.add(item("Hide"))
    menu.add(item("Quit"))
    assert labels(menu) == ["Show", "Hide", "Quit"]


def test_rebuild_on_empty_menu_keeps_it_empty():
    menu = TrayMenu()
    menu.rebuild()
    assert menu.items == []


def test_rebuild_keeps_plain_items():
    menu = TrayMenu(items=[item("Show"), item("Quit")])
    menu.rebuild()
    assert labels(menu) == ["Show", "Quit"]


def test_rebuild_drops_leading_separator():
    menu = TrayMenu(items=[sep(), item("Show")])
    menu.rebuild()
    assert labels(menu) == ["Show"]


def test_rebuild_drops_trailing_separator():
    menu = TrayMenu(items=[item("Show"), sep()])
    menu.rebuild()
    assert labels(menu) == ["Show"]


def test_rebuild_collapses_consecutive_separators():
    menu = TrayMenu(items=[item("Show"), sep(), sep(), sep(), item("Quit")])
    menu.rebuild()
    assert labels(menu) == ["Show", "|", "Quit"]


def test_rebuild_keeps_separator_between_items():
    menu = TrayMenu(items=[item("Show"), sep(), item("Quit")])
    menu.rebuild()
    assert labels(menu) == ["Show", "|", "Quit"]


def test_rebuild_drops_menu_of_only_separators():
    menu = TrayMenu(items=[sep(), sep(), sep()])
    menu.rebuild()
    assert menu.items == []


def test_rebuild_drops_item_with_empty_submenu():
    menu = TrayMenu(items=[item("Show"), item("More", submenu=[])])
    menu.rebuild()
    assert labels(menu) == ["Show"]


def test_rebuild_drops_item_whose_submenu_is_all_separators():
    menu = TrayMenu(items=[item("Show"), item("More", submenu=[sep(), sep()])])
    menu.rebuild()
    assert labels(menu) == ["Show"]


def test_rebuild_keeps_item_with_valid_submenu():
    menu = TrayMenu(items=[item("More", submenu=[item("A")])])
    menu.rebuild()
    assert labels(menu) == ["More"]
    assert [entry.label for entry in menu.items[0].submenu] == ["A"]


def test_rebuild_normalises_nested_submenu():
    inner = [sep(), item("A"), sep(), sep(), item("B"), sep()]
    menu = TrayMenu(items=[item("More", submenu=inner)])
    menu.rebuild()
    cleaned = menu.items[0].submenu
    assert [entry.label or "|" for entry in cleaned] == ["A", "|", "B"]


def test_rebuild_preserves_item_order():
    menu = TrayMenu(items=[item("A"), sep(), item("B"), item("C")])
    menu.rebuild()
    assert labels(menu) == ["A", "|", "B", "C"]


def test_rebuild_is_idempotent():
    menu = TrayMenu(items=[sep(), item("A"), sep(), sep(), item("B"), sep()])
    menu.rebuild()
    once = labels(menu)
    menu.rebuild()
    assert labels(menu) == once


def test_rebuild_does_not_mutate_original_items():
    inner = [sep(), item("A")]
    parent = item("More", submenu=inner)
    menu = TrayMenu(items=[parent])
    menu.rebuild()
    assert parent.submenu is inner
    assert inner[0].separator


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ([], []),
        ([sep()], []),
        ([item("A")], ["A"]),
        ([sep(), item("A"), sep()], ["A"]),
        ([item("A"), sep(), sep(), item("B")], ["A", "|", "B"]),
    ],
)
def test_rebuild_table(given, expected):
    menu = TrayMenu(items=given)
    menu.rebuild()
    assert labels(menu) == expected
