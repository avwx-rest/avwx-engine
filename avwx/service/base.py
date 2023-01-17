"""
Service base class
"""

# pylint: disable=too-few-public-methods,unsubscriptable-object

# stdlib
from socket import gaierror
from typing import Any, Optional, Tuple

# library
import httpx
import httpcore

# module
from avwx.exceptions import SourceError

_VALUE_ERROR = "'{}' is not a valid report type for {}. Expected {}"


TIMEOUT_ERRORS = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpcore.ReadTimeout,
    httpcore.WriteTimeout,
    httpcore.PoolTimeout,
)
CONNECTION_ERRORS = (gaierror, httpcore.ConnectError, httpx.ConnectError)
NETWORK_ERRORS = (
    httpcore.ReadError,
    httpcore.NetworkError,
    httpcore.RemoteProtocolError,
)


class Service:
    """Base Service class for fetching reports"""

    url: Optional[str] = None
    report_type: str
    _valid_types: Tuple[str, ...] = tuple()

    def __init__(self, report_type: str):
        if self._valid_types:
            if report_type not in self._valid_types:
                raise ValueError(
                    _VALUE_ERROR.format(
                        report_type, self.__class__.__name__, self._valid_types
                    )
                )
        self.report_type = report_type

    @property
    def root(self) -> Optional[str]:
        """Returns the service's root URL"""
        if self.url is None:
            return None
        url = self.url[self.url.find("//") + 2 :]
        return url[: url.find("/")]


class CallsHTTP:
    """Service supporting HTTP requests"""

    method: str = "GET"

    async def _call(  # pylint: disable=too-many-arguments
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        data: Any = None,
        timeout: int = 10,
        retries: int = 3,
    ) -> str:
        name = self.__class__.__name__
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                for _ in range(retries):
                    if self.method.lower() == "post":
                        resp = await client.post(
                            url, params=params, headers=headers, data=data
                        )
                    else:
                        resp = await client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        break
                    # Skip retries if remote server error
                    if resp.status_code >= 500:
                        raise SourceError(f"{name} server returned {resp.status_code}")
                else:
                    raise SourceError(f"{name} server returned {resp.status_code}")
        except TIMEOUT_ERRORS as timeout_error:
            raise TimeoutError(f"Timeout from {name} server") from timeout_error
        except CONNECTION_ERRORS as connect_error:
            raise ConnectionError(
                f"Unable to connect to {name} server"
            ) from connect_error
        except NETWORK_ERRORS as network_error:
            raise ConnectionError(
                f"Unable to read data from {name} server"
            ) from network_error
        return str(resp.text)
