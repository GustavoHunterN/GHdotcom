import json
from typing import Any


class Repo:
    """Domain model for a GitHub repository payload (no I/O)."""

    __slots__ = ("_data",)

    def __init__(self, **data: Any) -> None:
        self._data = dict(data)

    @classmethod
    def from_github(cls, payload: dict) -> "Repo":
        """Build a model from a GitHub API repository object."""
        return cls(**payload)

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(name)

    def __repr__(self) -> str:
        return str(self._data.get("name", "Repo"))

    def __str__(self) -> str:
        return str(self._data.get("name", ""))

    def as_db_row(self) -> dict[str, Any]:
        """Flat dict for persistence: complex values JSON-encoded, scalars as strings or None."""
        row: dict[str, Any] = {}
        for key, value in self._data.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value)
            elif value is None:
                row[key] = None
            else:
                row[key] = str(value)
        return row

    def keys(self) -> list[str]:
        return list(self._data.keys())
