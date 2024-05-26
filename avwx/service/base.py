"""All service classes are based on the base Service class. Implementation is mostly left to the other high-level subclasses."""

# stdlib
from __future__ import annotations

from socket import gaierror
from typing import Any, ClassVar

import httpcore

# library
import httpx

# module
from avwx.exceptions import SourceError

_TIMEOUT_ERRORS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpcore.ReadTimeout,
    httpcore.WriteTimeout,
    httpcore.PoolTimeout,
)
_CONNECTION_ERRORS = (gaierror, httpcore.ConnectError, httpx.ConnectError)
_NETWORK_ERRORS = (
    httpcore.ReadError,
    httpcore.NetworkError,
    httpcore.RemoteProtocolError,
)


class Service:
    """Base Service class for fetching reports."""

    report_type: str
    _url: ClassVar[str] = ""
    _valid_types: ClassVar[tuple[str, ...]] = ()

    def __init__(self, report_type: str):
        if self._valid_types and report_type not in self._valid_types:
            msg = f"'{report_type}' is not a valid report type for {self.__class__.__name__}. Expected {self._valid_types}"
            raise ValueError(msg)
        self.report_type = report_type

    @property
    def root(self) -> str | None:
        """Return the service's root URL."""
        if self._url is None:
            return None
        url = self._url[self._url.find("//") + 2 :]
        return url[: url.find("/")]


class CallsHTTP:
    """Service mixin supporting HTTP requests."""

    method: ClassVar[str] = "GET"

    async def _call(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        data: Any = None,
        timeout: int = 10,
        retries: int = 3,
    ) -> str:
        name = self.__class__.__name__
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                for _ in range(retries):
                    if self.method.lower() == "post":
                        resp = await client.post(url, params=params, headers=headers, data=data)
                    else:
                        resp = await client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        break
                    # Skip retries if remote server error
                    if resp.status_code >= 500:
                        msg = f"{name} server returned {resp.status_code}"
                        raise SourceError(msg)
                else:
                    msg = f"{name} server returned {resp.status_code}"
                    raise SourceError(msg)
        except _TIMEOUT_ERRORS as timeout_error:
            msg = f"Timeout from {name} server"
            raise TimeoutError(msg) from timeout_error
        except _CONNECTION_ERRORS as connect_error:
            msg = f"Unable to connect to {name} server"
            raise ConnectionError(msg) from connect_error
        except _NETWORK_ERRORS as network_error:
            msg = f"Unable to read data from {name} server"
            raise ConnectionError(msg) from network_error
        return str(resp.text)
