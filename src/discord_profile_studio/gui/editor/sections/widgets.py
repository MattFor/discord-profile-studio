import queue
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from threading import Thread
from tkinter import simpledialog, ttk

from discord_profile_studio.auth.encrypted_store import EncryptedFileStore
from discord_profile_studio.auth.store import TokenStore, open_store
from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.core.exceptions import StudioError, TokenNotFoundError, WidgetError
from discord_profile_studio.gui.components.scrollable import ScrollableFrame
from discord_profile_studio.gui.editor.fields import LabelledEntry
from discord_profile_studio.gui.editor.sections.base import EditorSection
from discord_profile_studio.gui.sections import Section
from discord_profile_studio.models.widget import Widget, WidgetField
from discord_profile_studio.widgets.api import WidgetApi, push_all, token_account
from discord_profile_studio.widgets.spec import fit, problems

POLL_MS = 50
STATUS_WRAP = 520


@dataclass(slots=True)
class _Card:
    widget: Widget
    frame: ttk.Labelframe
    entries: dict[str, LabelledEntry]


def _in_background[T](
    owner: tk.Misc,
    work: Callable[[], T],
    done: Callable[[T | Exception], None],
) -> None:
    # Discord calls run off the Tk thread, after() hands the result back to it
    results: queue.Queue[T | Exception] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            results.put(work())
        except Exception as e:
            results.put(e)

    def poll() -> None:
        try:
            result = results.get_nowait()
        except queue.Empty:
            owner.after(POLL_MS, poll)
            return

        done(result)

    Thread(target=run, daemon=True, name="dps-widgets").start()
    owner.after(POLL_MS, poll)


def _describe(error: Exception) -> str:
    return str(error) if isinstance(error, StudioError) else f"Unexpected error: {error!r}"


class WidgetsSection(EditorSection):
    section = Section.WIDGETS

    def build(self) -> None:
        self._cards: list[_Card] = []
        self._store: TokenStore | None = None

        bar = ttk.Frame(self)
        bar.pack(fill="x")

        self.application = LabelledEntry(bar, "Application ID", limit=20)
        self.application.build()
        self.application.pack(side="left", fill="x", expand=True)

        self.add_button = ttk.Button(bar, text="Add widget", command=self.fetch)
        self.add_button.pack(side="left", padx=(8, 0))

        self.scroll = ScrollableFrame(self)
        self.scroll.build()
        self.scroll.pack(fill="both", expand=True, pady=8)

        footer = ttk.Frame(self)
        footer.pack(fill="x")

        self.push_button = ttk.Button(footer, text="Push widgets", command=self.push)
        self.push_button.pack(side="left")

        self.status = tk.StringVar()
        ttk.Label(footer, textvariable=self.status, wraplength=STATUS_WRAP, justify="left").pack(
            side="left",
            padx=8,
        )

        self.read()

    def read(self) -> None:
        self.from_model(self.state_store.current.widgets)

    def write(self) -> None:
        self.state_store.current.widgets = self.to_model()
        self.state_store.dirty = True
        self.state_store.notify()

    def to_model(self) -> list[Widget]:
        return [
            Widget(
                card.widget.application_id,
                card.widget.name,
                [
                    WidgetField(field.name, field.kind, card.entries[field.name].variable.get())
                    for field in card.widget.fields
                ],
            )
            for card in self._cards
        ]

    def from_model(self, widgets: list[Widget]) -> None:
        for card in self._cards:
            card.frame.destroy()

        self._cards = []

        for widget in widgets:
            self.add_widget(widget)

    def add_widget(self, widget: Widget) -> None:
        title = f"{widget.name or 'Widget'} ({widget.application_id})"
        frame = ttk.Labelframe(self.scroll.inner, text=title, padding=8)
        frame.pack(fill="x", pady=(0, 8))
        card = _Card(widget, frame, {})

        for field in widget.fields:
            entry = LabelledEntry(frame, f"{field.name} ({field.kind.name.lower()})")
            entry.build()
            entry.variable.set(field.value)
            entry.variable.trace_add("write", lambda *_: self.write())
            entry.pack(fill="x", pady=2)
            card.entries[field.name] = entry

        remove = ttk.Button(
            frame,
            text="Remove",
            command=lambda: self.remove_widget(self._cards.index(card)),
        )
        remove.pack(anchor="e", pady=(4, 0))
        self._cards.append(card)

    def remove_widget(self, index: int) -> None:
        self._cards.pop(index).frame.destroy()
        self.write()

    def fetch(self) -> None:
        application_id = self.application.variable.get().strip()

        if not application_id.isdigit():
            self.status.set("Enter the numeric ID of the widget's application")
            return

        try:
            store = self._tokens()
            found = None if store is None else self._token(store, application_id)
        except StudioError as e:
            self.status.set(str(e))
            return

        if store is None or found is None:
            return

        token, fresh = found
        known = next((w.fields for w in self.to_model() if w.application_id == application_id), [])

        def work() -> Widget:
            api = WidgetApi(token)
            application = api.application()

            if application.id != application_id:
                msg = f"that bot token belongs to application {application.id}"
                raise WidgetError(msg)

            if fresh:
                store.set(token_account(application_id), token)

            return Widget(
                application_id, application.name, fit(known, api.config(application_id).fields)
            )

        self._busy(f"Fetching application {application_id}...")
        _in_background(self, work, self._fetched)

    def push(self) -> None:
        widgets = self.to_model()

        if not widgets:
            self.status.set("Add a widget first")
            return

        try:
            store = self._tokens()
        except StudioError as e:
            self.status.set(str(e))
            return

        if store is None:
            return

        def work() -> int:
            push_all(
                widgets, lambda application_id: WidgetApi(store.get(token_account(application_id)))
            )
            return len(widgets)

        self._busy("Pushing...")
        _in_background(self, work, self._pushed)

    def _fetched(self, result: Widget | Exception) -> None:
        self._idle()

        if isinstance(result, Exception):
            self.status.set(_describe(result))
            return

        widgets = self.to_model()
        ids = [widget.application_id for widget in widgets]

        if result.application_id in ids:
            widgets[ids.index(result.application_id)] = result
        else:
            widgets.append(result)

        self.from_model(widgets)
        self.write()
        self.application.variable.set("")

        missing = len(problems(result.fields, {field.name: field.kind for field in result.fields}))
        self.status.set(
            f"Added {result.name}" + (f", {missing} value(s) to fill in" if missing else "")
        )

    def _pushed(self, result: int | Exception) -> None:
        self._idle()
        self.status.set(
            _describe(result)
            if isinstance(result, Exception)
            else f"Pushed {result} widget(s) to your profile"
        )

    def _tokens(self) -> TokenStore | None:
        if self._store is None:
            store = open_store()

            if isinstance(store, EncryptedFileStore) and store.locked:
                passphrase = simpledialog.askstring(
                    "Token store",
                    "Passphrase of the encrypted token store",
                    show="*",
                    parent=self,
                )

                if passphrase is None:
                    return None

                store.unlock(passphrase)

            self._store = store

        return self._store

    def _token(self, store: TokenStore, application_id: str) -> tuple[Token, bool] | None:
        try:
            return store.get(token_account(application_id)), False
        except TokenNotFoundError:
            secret = simpledialog.askstring(
                "Bot token",
                f"Bot token of application {application_id}",
                show="*",
                parent=self,
            )

        if not secret or not secret.strip():
            return None

        return Token(kind=TokenKind.BOT, access_token=secret.strip()), True

    def _busy(self, message: str) -> None:
        self.status.set(message)

        for button in (self.add_button, self.push_button):
            button.state(["disabled"])

    def _idle(self) -> None:
        for button in (self.add_button, self.push_button):
            button.state(["!disabled"])
