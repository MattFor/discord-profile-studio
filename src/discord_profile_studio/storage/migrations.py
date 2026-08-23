from typing import Any

SCHEMA_VERSION = 1


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError
