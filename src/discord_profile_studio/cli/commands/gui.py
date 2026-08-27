import tkinter as tk
from threading import Thread

import pystray
import typer
from PIL import Image, ImageDraw

app = typer.Typer(no_args_is_help=False, invoke_without_command=True)


def _create_tray_icon(
    root: tk.Tk,
    *,
    favourite: str | None,
    on_show: callable,
    on_quit: callable,
) -> pystray.Icon:
    image = Image.new("RGBA", (64, 64), (20, 20, 20, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (8, 8, 56, 56),
        radius=12,
        fill=(255, 20, 130, 255),
    )

    draw.text(
        (32, 32),
        "D",
        fill="white",
        anchor="mm",
    )

    menu = pystray.Menu(
        pystray.MenuItem(
            "Show",
            lambda icon, item: root.after(0, on_show),
            default=True,
        ),
        pystray.MenuItem(
            "Quit",
            lambda icon, item: root.after(0, on_quit),
        ),
    )

    title = "Discord Profile Studio"
    if favourite:
        title += f" — {favourite}"

    return pystray.Icon(
        "discord-profile-studio",
        image,
        title,
        menu,
    )


def _launch(
    *,
    favourite: str | None,
    minimized: bool,
    tray: bool,
) -> None:
    root = tk.Tk()
    root.title("Discord Profile Studio")
    root.geometry("700x450")
    root.minsize(500, 300)

    favourite_var = tk.StringVar(value=favourite or "No favourite selected")

    frame = tk.Frame(root, padx=24, pady=24)
    frame.pack(fill="both", expand=True)

    title = tk.Label(
        frame,
        text="Discord Profile Studio",
        font=("TkDefaultFont", 18, "bold"),
    )
    title.pack(pady=(10, 4))

    favourite_label = tk.Label(
        frame,
        text="Favourite:",
    )
    favourite_label.pack()

    favourite_value = tk.Label(
        frame,
        textvariable=favourite_var,
        font=("TkDefaultFont", 12, "bold"),
    )
    favourite_value.pack(pady=(4, 20))

    status_var = tk.StringVar(value="Ready")

    status = tk.Label(
        frame,
        textvariable=status_var,
        fg="gray",
    )
    status.pack(side="bottom")

    tray_icon: pystray.Icon | None = None

    def show() -> None:
        root.deiconify()
        root.lift()
        root.focus_force()
        status_var.set("Ready")

    def hide() -> None:
        root.withdraw()
        status_var.set("Running in tray")

    def quit_app() -> None:
        nonlocal tray_icon

        if tray_icon is not None:
            tray_icon.stop()

        root.destroy()

    def on_close() -> None:
        if tray:
            hide()
        else:
            quit_app()

    root.protocol("WM_DELETE_WINDOW", on_close)

    if tray:
        tray_icon = _create_tray_icon(
            root,
            favourite=favourite,
            on_show=show,
            on_quit=quit_app,
        )

        Thread(
            target=tray_icon.run,
            daemon=True,
            name="dps-tray",
        ).start()

    if minimized:
        root.after(100, hide)

    root.mainloop()


@app.callback(invoke_without_command=True)
def launch(
    favourite: str | None = typer.Option(
        None,
        "--favourite",
        "-f",
    ),
    minimized: bool = typer.Option(
        False,
        "--minimized",
    ),
    tray: bool = typer.Option(
        True,
        "--tray/--no-tray",
    ),
) -> None:
    _launch(
        favourite=favourite,
        minimized=minimized,
        tray=tray,
    )
