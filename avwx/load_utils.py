"""Data load utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, ItemsView, Iterator, ValuesView


class LazyLoad:
    """Lazy load a dictionary from the JSON data cache."""

    source: Path
    _data: dict[str, Any] | None = None

    def __init__(self, filename: str):
        self.source = Path(__file__).parent.joinpath("data", "files", f"{filename}.json")

    def _load(self) -> None:
        with self.source.open(encoding="utf8") as fin:
            self._data = json.load(fin)

    def _check(self) -> None:
        if self._data is None:
            self._load()

    @property
    def data(self) -> dict[str, Any]:
        return self._data or {}

    def __getitem__(self, key: str) -> Any:
        self._check()
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        self._check()
        return key in self.data

    def __len__(self) -> int:
        self._check()
        return len(self.data)

    def __iter__(self) -> Iterator[str]:
        self._check()
        yield from self.data

    def items(self) -> ItemsView:
        self._check()
        return self.data.items()

    def values(self) -> ValuesView:
        self._check()
        return self.data.values()


# LazyCalc lets us avoid the global keyword
class LazyCalc:
    """Delay data calculation until needed."""

    _func: Callable
    _value: Any | None = None

    def __init__(self, func: Callable):
        self._func = func

    @property
    def value(self) -> Any:
        if self._value is None:
            self._value = self._func()
        return self._value
