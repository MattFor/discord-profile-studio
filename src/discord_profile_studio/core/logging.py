import logging


def setup(*, verbose: bool = False) -> None:
    raise NotImplementedError


def get(name: str) -> logging.Logger:
    raise NotImplementedError
