"""
Data load utilities
"""

# pylint: disable=missing-function-docstring

import json
from collections.abc import ItemsView, ValuesView
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional


class LazyLoad:
    """Lazy load a dictionary from the JSON data cache"""

    source: Path
    _data: Optional[Dict[str, Any]] = None

    def __init__(self, filename: str):
        self.source = Path(__file__).parent.joinpath("data", f"{filename}.json")

    def _load(self):
        self._data = json.load(self.source.open(encoding="utf8"))

    def _check(self):
        if self._data is None:
            self._load()

    @property
    def data(self) -> Dict[str, Any]:
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

    def __iter__(self) -> Iterable[str]:
        self._check()
        for key in self.data:
            yield key

    def items(self) -> ItemsView:
        self._check()
        return self.data.items()

    def values(self) -> ValuesView:
        self._check()
        return self.data.values()


# LazyCalc lets us avoid the global keyword
class LazyCalc:
    """Delay data calculation until needed"""

    # pylint: disable=too-few-public-methods,missing-function-docstring

    _func: Callable
    _value: Optional[Any] = None

    def __init__(self, func: Callable):
        self._func = func  # type: ignore

    @property
    def value(self) -> Any:
        if self._value is None:
            self._value = self._func()
        return self._value
