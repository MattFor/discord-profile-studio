import tkinter as tk
from tkinter import ttk

# Tk 8.6 on X11 reports the wheel as buttons 4 and 5 instead of <MouseWheel>
WHEEL_EVENTS = ("<MouseWheel>", "<Button-4>", "<Button-5>")
WHEEL_UP_BUTTON = 4


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.inner = ttk.Frame(self.canvas)

    def build(self) -> None:
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        background = ttk.Style(self).lookup("TFrame", "background")

        self.canvas.configure(yscrollcommand=scrollbar.set, background=background)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", lambda _: self._fit_region())
        self.canvas.bind(
            "<Configure>", lambda event: self.canvas.itemconfigure(window, width=event.width)
        )

        # Wheel only scrolls this frame while the pointer is over it
        self.bind("<Enter>", lambda _: [self.bind_all(name, self._wheel) for name in WHEEL_EVENTS])
        self.bind("<Leave>", lambda _: [self.unbind_all(name) for name in WHEEL_EVENTS])

    def _fit_region(self) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _wheel(self, event: "tk.Event[tk.Misc]") -> None:
        up = event.num == WHEEL_UP_BUTTON or event.delta > 0

        self.canvas.yview_scroll(-1 if up else 1, "units")
