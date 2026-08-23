from pathlib import Path
from tkinter import PhotoImage


class ImageStore:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.images: dict[str, PhotoImage] = {}

    def load(self, key: str) -> PhotoImage:
        raise NotImplementedError

    def rounded(self, key: str, size: int, radius: int) -> PhotoImage:
        raise NotImplementedError

    def placeholder(self, size: int) -> PhotoImage:
        raise NotImplementedError
