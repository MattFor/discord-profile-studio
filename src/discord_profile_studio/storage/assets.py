from pathlib import Path


class AssetCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, key: str) -> Path:
        raise NotImplementedError

    def fetch(self, url: str) -> Path:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
