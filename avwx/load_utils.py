"""
Data load utilities
"""

# pylint: disable=missing-function-docstring

import json
from collections.abc import KeysView, ValuesView
from pathlib import Path
from typing import Callable, Iterable, Optional


class LazyLoad:
    """Lazy load a dictionary from the JSON data cache"""

    source: Path
    data: Optional[dict] = None

    def __init__(self, filename: str):
        self.source = Path(__file__).parent.joinpath("data", f"{filename}.json")

    def _load(self):
        self.data = json.load(self.source.open(encoding="utf8"))

    def __getitem__(self, key: str) -> object:
        if not self.data:
            self._load()
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        if not self.data:
            self._load()
        return key in self.data

    def __len__(self) -> int:
        if not self.data:
            self._load()
        return len(self.data)

    def __iter__(self) -> Iterable[str]:
        if not self.data:
            self._load()
        for key in self.data:
            yield key

    def items(self) -> KeysView:
        if not self.data:
            self._load()
        return self.data.items()

    def values(self) -> ValuesView:
        if not self.data:
            self._load()
        return self.data.values()


# LazyCalc lets us avoid the global keyword
class LazyCalc:
    """Delay data calculation until needed"""

    # pylint: disable=too-few-public-methods,missing-function-docstring

    func: Callable
    _value: object = None

    def __init__(self, func: Callable):
        self.func = func

    @property
    def value(self) -> object:
        if self._value is None:
            self._value = self.func()
        return self._value
